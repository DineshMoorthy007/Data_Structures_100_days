# Python DSA Codes

Practical, standalone Python scripts that explain data structures, algorithms, and system-design-inspired patterns.

The goal is to help learners understand **what each concept does**, **why it is useful**, and **where it appears in real systems**.

## Table of contents

- [What this repository offers](#what-this-repository-offers)
- [Core concepts explained simply](#core-concepts-explained-simply)
- [Repository structure](#repository-structure)
- [Topic map with representative files](#topic-map-with-representative-files)
- [How to run examples](#how-to-run-examples)
- [Suggested learning path](#suggested-learning-path)
- [Contributing](#contributing)
- [License](#license)

## What this repository offers

- Script-based examples you can run directly with Python
- Simple, readable implementations of core DSA concepts
- Real-world style use cases (caching, routing, scheduling, graph traversal, synchronization, and more)
- A broad range of topics from fundamentals to advanced system-oriented patterns

## Core concepts explained simply

- **Array/List**: Store ordered items; good for fast indexed access.
- **Stack (LIFO)**: Last item added is removed first; useful for undo, parsing, and validation.
- **Queue (FIFO)**: First item added is removed first; useful for task processing and buffering.
- **Hash Map/Dictionary**: Key-value lookup in near constant time; useful for indexing and routing.
- **Linked Structure**: Nodes connected by pointers; useful for dynamic insertion/deletion patterns.
- **Tree**: Hierarchical structure; useful for search, ordering, and prefix-based retrieval.
- **Heap/Priority Queue**: Efficiently fetch min/max priority item; useful for scheduling and shortest-path problems.
- **Graph**: Models relationships between entities; useful for networks, dependencies, and pathfinding.
- **Dynamic Programming**: Reuses solved subproblems; useful for optimization and counting problems.
- **Probabilistic Structures**: Trade exactness for speed/memory (for example Bloom/Cuckoo/HyperLogLog-style approaches).
- **Distributed Consistency Patterns**: Demonstrates ideas behind consensus, replication, and conflict resolution.

## Repository structure

- All examples are currently in the repository root as individual `.py` files.
- Most files are self-contained and include demonstration code/output comments.
- File names describe the main concept or engine simulated in that script.

### Naming style note

Some files use descriptive "engine-style" names to reflect real-world use cases, while others use classic DSA naming. All are intended as learning-focused examples.

## Topic map with representative files

### Fundamentals
- `LIFO_Stack_Wrapper.py`
- `Balanced_Brackets_Validator.py`
- `Fixed_Size_Ring_Buffer.py`
- `Node_Based_Pointer_Chain.py`
- `Binary_Search_Tree_Insertion.py`

### Search, sort, and optimization
- `Recursive_Divide_And_Conquer_Sort.py`
- `Three_Pointer_Pivot.py`
- `Memoized_Fibonacci_Sequence.py`
- `Space_Optimized_Matrix_Edit_Distance.py`

### Graph algorithms and pathfinding
- `Simple_Social_Network_Graph.py`
- `Friends_of_Friends_Finder.py`
- `Grid_Based_A*_Pathfinding_Engine.py`
- `Kruskal_MST_Engine_With_Union_FInd.py`
- `Single_Pass_Bridge_Detector.py`

### Caching and memory-efficient structures
- `Memory_Cache_From_Scratch.py`
- `Hash_Map_&_Doubly_Linked_List_Cache_Engine.py`
- `Production_Grade_LRU_K_Cache_Engine.py`
- `Production_Grade_Space_Efficient_Bloom_Filter.py`
- `Cuckoo_Filter_with_Fingerprint_Eviction_&_Deletions.py`

### Concurrency, reliability, and distributed systems
- `Thread_Safe_Bounded_Queue_using_Condition_Variables.py`
- `Thread_Safe_Writer_Preference_Read_Write_Lock.py`
- `Crash_Resistant_Write_Ahead_Log_Engine.py`
- `Distributed_Raft_Leader_Election_State_Machine.py`
- `Production_Grade_Transactional_Outbox_&_Relay_Engine.py`

## How to run examples

### Requirements

- Python 3.8+ recommended
- No external dependencies required for most scripts

### Quick start

1. Clone the repository:

   ```bash
   git clone https://github.com/DineshMoorthy007/Python_DSA_Codes.git
   cd Python_DSA_Codes
   ```

2. Run any script:

   ```bash
   python Balanced_Brackets_Validator.py
   python Grid_Based_A*_Pathfinding_Engine.py
   ```

3. Read the code and modify inputs to experiment with behavior.

### Tips for learning from each script

- Read the top-level function/class names first.
- Run the script once before modifying it.
- Change one input at a time and re-run to observe behavior.
- Compare multiple scripts from the same topic to see pattern differences.

## Suggested learning path

1. Start with stack, queue, dictionary, and linked structure examples.
2. Move to trees, heaps, recursion, and dynamic programming.
3. Continue with graph traversal and shortest-path algorithms.
4. Explore probabilistic and distributed-system-inspired implementations.

## Contributing

Contributions are welcome. Prefer clear naming, small focused examples, and simple explanations in code.

## License

This repository is intended for learning and educational use.
