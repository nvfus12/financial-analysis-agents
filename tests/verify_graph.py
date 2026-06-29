import os
import sys
import logging

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_graph")

def main():
    logger.info("Initializing database migrations first...")
    from src.infrastructure.database.migrations import run_migrations
    run_migrations()
    
    logger.info("Building and compiling LangGraph state machine...")
    try:
        from src.agents.graph import build_graph
        graph = build_graph()
        logger.info("LangGraph compiled successfully!")
        
        # Print the nodes in the graph
        logger.info("Compiled Graph Nodes:")
        for node_name in graph.nodes.keys():
            print(f"- {node_name}")
            
        logger.info("Verification complete. No structural errors found in the graph.")
    except Exception as e:
        logger.error(f"Failed to compile LangGraph: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
