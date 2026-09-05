from mistral_rag import rag_query 


q = "kto to kardiolog?"
ctx, src = rag_query(q, k=1)
print("Źródła:", src)
print("---\n".join(ctx))