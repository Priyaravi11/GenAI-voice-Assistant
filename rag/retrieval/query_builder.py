class QueryBuilder:
    
    def build(
        self,
        query: str,
        category: str | None = None,
        customer_id: str | None = None
    ) -> dict:

        return {
            "query": query.strip(),
            "category": category,
            "customer_id": customer_id
        }