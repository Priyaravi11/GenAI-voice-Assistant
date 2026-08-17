class ContextBuilder:
    
    def build(self, results: dict) -> dict:

        if not results.get("documents") or not results["documents"][0]:
            return {
                "success": False,
                "documents": [],
                "reason": "No relevant knowledge found"
            }

        documents = []

        retrieved_documents = results["documents"][0]
        retrieved_metadatas = results["metadatas"][0]
        retrieved_distances = results.get("distances", [[]])[0]

        for i, (content, metadata) in enumerate(
            zip(retrieved_documents, retrieved_metadatas)
        ):

            distance = (
                retrieved_distances[i]
                if i < len(retrieved_distances)
                else None
            )

            documents.append({
                "content": content,
                "category": metadata.get("category"),
                "customer_id": metadata.get("customer_id"),
                "distance": distance
            })

        return {
            "success": True,
            "documents": documents
        }