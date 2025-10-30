"""Backend configuration for file storage using DeepAgents patterns."""

from deepagents.backends import StateBackend, StoreBackend, CompositeBackend


def create_finance_backend(store=None):
    """
    Create a CompositeBackend for financial data management.

    Routes:
    - /financial_data/ -> StoreBackend (persistent user financial data)
    - /user_profiles/ -> StoreBackend (persistent user preferences/config)
    - /reports/ -> StoreBackend (persistent analysis reports)
    - /analysis_history/ -> StoreBackend (past analyses)
    - Everything else -> StateBackend (ephemeral working files)

    Args:
        store: LangGraph BaseStore instance for persistent storage.
               If None, all routes will use StateBackend.

    Returns:
        CompositeBackend instance
    """
    if store is None:
        # No persistent storage, everything is ephemeral
        return lambda rt: StateBackend(rt)

    # Create CompositeBackend with routing
    def backend_factory(runtime):
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={
                "/financial_data/": StoreBackend(runtime, store=store),
                "/user_profiles/": StoreBackend(runtime, store=store),
                "/reports/": StoreBackend(runtime, store=store),
                "/analysis_history/": StoreBackend(runtime, store=store),
            }
        )

    return backend_factory


def get_default_backend():
    """Get default backend (StateBackend only, no persistence)."""
    return lambda rt: StateBackend(rt)
