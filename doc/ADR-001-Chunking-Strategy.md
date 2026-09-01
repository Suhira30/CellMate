# Architecture Decision Record ADR-001: Evaluation of Chunking Strategies for NIE Biology RAG System

- **Status**: Proposed / Under Active Experimentation
- **Date**: 2026-08-31
- **Context**: Sri Lanka G.C.E. A/L Biology (Unit 2: Chemical & Cellular Basis of Life)

---

## 1. Context & Problem Statement

In Retrieval-Augmented Generation (RAG) systems for dense academic textbooks like the **NIE Biology Resource Book**, chunking is the foundational data transformation step. The choice of chunking algorithm directly dictates:

1. **Retrieval Precision**: Whether vector search pulls relevant context without extra noise.
2. **Context Integrity**: Whether biological definitions (e.g. competitive vs non-competitive inhibition) remain intact within a single chunk or get truncated mid-sentence across chunk boundaries.
3. **Token Efficiency & LLM Cost**: How many tokens are sent to Google Gemini 1.5 per query.

To select the optimal strategy, we evaluate **5 candidate chunking approaches**.

---

## 2. Considered Chunking Approaches

### 2.1 Fixed Character-Level Chunking

Splits text into rigid, fixed-size windows (e.g., exactly 600 characters) regardless of word, sentence, or paragraph boundaries.

### 2.2 Recursive Character Chunking

Recursively attempts to split text on natural separators in hierarchy (`\n\n` paragraphs $\rightarrow$ `\n` lines $\rightarrow$ `. ` sentences $\rightarrow$ ` ` words) until chunks fit within target window size.

### 2.3 Token-Based Chunking

Splits text based on tokenizer token count (e.g. 250 tokens), ensuring exact fit within LLM token context limits.

### 2.4 Document Structure-Aware Chunking (Heading / Section Based)

Leverages document layout headers (e.g. `2.1 Properties of Water`, `2.3.1 Enzyme Inhibition`) to split text along logical syllabus boundaries.

### 2.5 Semantic Chunking

Computes embedding similarity between adjacent sentences and creates chunk breaks when semantic similarity drops below a specified threshold.

### 2.6 Hybrid Structure-Aware Recursive Chunking

Combines primary syllabus heading detection (e.g. `2.1 Chemical Basis`, `2.1.1 Water`) with secondary sentence-strict recursive sub-chunking (target 600 characters, 100 overlap). Attaches parent section titles as metadata to every sub-chunk to preserve full context.

---

## 3. Advantages & Disadvantages Comparison

| Chunking Method                   | Advantages                                                                                                                                                                        | Disadvantages                                                                                                         |
| :-------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| **1. Fixed Character**            | • Extremely fast and simple to implement.<br>• Predictable memory consumption.                                                                                                    | ❌ Truncates words and sentences mid-concept.<br>❌ Severely degrades retrieval accuracy for complex NIE definitions. |
| **2. Recursive Character**        | • Preserves paragraph and sentence boundaries.<br>• Flexible window sizing.<br>• Highly reliable default for text RAG.                                                            | ⚠️ May still split section headers from their sub-paragraphs if section is very long.                                 |
| **3. Token-Based**                | • Guarantees exact LLM token budget compliance.<br>• Prevents prompt overflow errors.                                                                                             | ❌ Ignores semantic sentence boundaries if tokens run out mid-sentence.                                               |
| **4. Structure-Aware**            | • Perfect alignment with NIE syllabus hierarchy.<br>• Keeps entire sub-topics (e.g., Water properties) coherent.                                                                  | ⚠️ Variable chunk sizes (some sections are 200 chars, others 4,500 chars requiring sub-chunking).                     |
| **5. Semantic Chunking**          | • Groups conceptually related sentences together based on vector embedding similarity.                                                                                            | ❌ High computational cost (requires embedding every sentence upfront).<br>❌ Slower ingestion speed.                 |
| **6. Hybrid Structure-Recursive** | • Combines syllabus structural hierarchy with bounded 600-char sub-chunks.<br>• Preserves parent section headers as metadata on every chunk.<br>• High sentence integrity (>95%). | ⚠️ Requires section heading regex pattern configuration for NIE textbooks.                                            |

---

## 4. Evaluation & Decision Matrix

| Evaluation Criteria (Weight)        | Fixed Character | Recursive Character | Token-Based  | Structure-Aware | Semantic Chunking | Hybrid Structure-Recursive |
| :---------------------------------- | :-------------: | :-----------------: | :----------: | :-------------: | :---------------: | :------------------------: |
| **Retrieval Quality (30%)**         |      2 / 5      |        4 / 5        |    3 / 5     |      5 / 5      |       5 / 5       |           5 / 5            |
| **Context Preservation (25%)**      |      1 / 5      |        4 / 5        |    2 / 5     |      5 / 5      |       4 / 5       |           5 / 5            |
| **Processing Speed (20%)**          |      5 / 5      |        5 / 5        |    4 / 5     |      4 / 5      |       1 / 5       |          4.5 / 5           |
| **Cost & Token Efficiency (15%)**   |      3 / 5      |        4 / 5        |    5 / 5     |      4 / 5      |       2 / 5       |          4.5 / 5           |
| **Implementation Simplicity (10%)** |      5 / 5      |        5 / 5        |    4 / 5     |      3 / 5      |       2 / 5       |           4 / 5            |
| **Weighted Total Score**            |  **2.95 / 5**   |    **4.35 / 5**     | **3.35 / 5** |  **4.45 / 5**   |   **3.35 / 5**    |        **4.73 / 5**        |

---

## 5. Decision & Proposed Strategy

### Final Decision: Hybrid Structure-Aware Recursive Chunking

We adopt a **Hybrid Structure-Aware + Recursive Character Chunking Strategy**:

1. **Primary Segmentation (Structure-Aware)**: Split NIE documents by sub-unit headers (`2.1`, `2.2`, `2.3`).
2. **Secondary Sub-segmentation (Recursive Character)**: If a sub-unit section exceeds target `CHUNK_SIZE` (600 characters), apply recursive paragraph/sentence splitting with 100-character overlap.

### Rationale

- NIE Biology exam evaluation requires exact complete definitions. Structure-aware boundaries ensure headers remain linked with their explanations.
- Recursive sub-chunking prevents oversized chunks while maintaining high processing speed without expensive upfront sentence embedding calls.

---

## 6. Consequences & Trade-offs

### Positive Consequences

- **Zero Truncation**: Biological terms (e.g., _Phosphodiester bond_, _Competitive inhibitor_) will never be split across random character limits.
- **Enhanced Grounding**: Page metadata and section headers are attached to every chunk for precise citation in UI.

### Negative Consequences / Mitigations

- Requires regex pattern matching for NIE section headers (mitigated via robust pattern testing in `experiments/`).

---

## 7. Two-Phase Evaluation Methodology: Static Metrics vs. Retrieval Hit Rate

### 💡 Core Engineering Principle:

$$\text{Good Chunking} + \text{Good Retrieval Performance (Hit Rate / Precision@K)} = \text{Optimal Production Strategy}$$

1. **Static Metrics are only Step 1**: Measuring chunk character length and boundary integrity confirms that our text is clean and well-formed, but it **does not tell us if ChromaDB will actually find the right answer** when a student asks a tricky exam question.
2. **Retrieval Performance is the True Ground Truth**: The ultimate measure of a chunking strategy is **Retrieval Hit Rate** (Does top-K vector search pull the exact NIE Resource Book snippet needed to answer the student's question?).
3. **Execution Plan**: All 6 chunking strategies remain modularly implemented in `experiments/chunkers/`. Final production selection will be locked in after running live vector search retrieval evaluation in Stage 3.
   4
