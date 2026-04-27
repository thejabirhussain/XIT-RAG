from qdrant_client import QdrantClient

client = QdrantClient(
    host="f6d63c06-a427-4edb-843d-5f2d616aa56f.europe-west3-0.gcp.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjNmMWYyNDEtMjA1ZC00ZGE0LWExZWUtNjdhYzVkMWU4YTA1In0.KpdD0CKDc6f7Oxupbvm_woDmAoCAHf4sv-1y4fKgWKk",
    https=True,
    port=443
)

collections = client.get_collections()
print(collections)