from mistral_rag import rag_query          
from mistral_server import generate_text   
import time

# prompt = f"""Pacjent skarży się na swędzącą, łuszczącą się wysypkę na skórze przedramion oraz pojawienie się trudno gojących się zmian skórnych. W badaniach laboratoryjnych zauważono podwyższony poziom eozynofilów oraz nieprawidłowy wynik testu alergicznego wskazujący na reakcję nadwrażliwości skórnej. Do jakiego lekarza powinna udać się osoba?"""

prompt = f"""Anuria - what is it?"""

rag_chunks, rag_sources = rag_query(prompt, k=3)

context = "\n".join(rag_chunks)
full_prompt = f"""### Context:
{context}

### Question:
{prompt}

### Answer:"""

start = time.time()
generated = generate_text(full_prompt)
end = time.time()

print("\nContext from RAG:\n")
print(context)
print("\nGenerated answer:\n")
print(generated)
print(f"\nTime taken: {end - start:.2f} seconds.")
print("\nSources:", set(rag_sources))
