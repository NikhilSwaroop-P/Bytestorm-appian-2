import voyageai

vo = voyageai.Client(api_key="pa-XQAgthfL8fQaoJWkagJgqOj6BTRbRlTKW-z-W_FLaDq")

def rerank_products(indices, metadata, current_text, k = 50):

    retrieved_results = []
    for index in indices:
        retrieved_results.append(metadata[index])

    documents = []
    for i, result in enumerate(retrieved_results):
        documents.append('<'+str(i)+'> ' + result['text_input'])
    reranking = vo.rerank(
        query=current_text,
        documents=documents,
        model="rerank-2",
        top_k=k
    )
    result = reranking.results
    reranked_indices = []
    for r in result:
        idx = int(r.document.split('<')[1].split('>')[0])
        reranked_indices.append(indices[idx])
    return reranked_indices, metadata

if __name__ == "__main__":
    # Example usage
    indices = [ 1, 2, 3, 0]  # Example indices
    metadata = [
        {"text_input": "Product A description electronics"},
        {"text_input": "Product B description mechanics"},
        {"text_input": "Product C description"},
        {"text_input": "Product D description"},
        {"text_input": "Product E description"}
    ]
    current_text = "Find products related to electronics"
    
    reranked_indices = rerank_products(indices, metadata, current_text)
    print("Reranked Indices:", reranked_indices)