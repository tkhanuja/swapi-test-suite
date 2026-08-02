# from utils import SwapiClient

# def test_character_film_bidirectional_link():
#     client = SwapiClient()
    
#     # Fetch Luke Skywalker (ID 1)
#     person_res = client.get("people/1/")
#     assert person_res.status_code == 200
#     person_data = person_res.json()
    
#     # Extract the first film URL
#     film_url = person_data["films"][0]
    
#     # Fetch the film resource directly via its nested URL
#     film_res = client.get_by_url(film_url)
#     assert film_res.status_code == 200
#     film_data = film_res.json()
    
#     # Assert that the film references the original character back
#     assert person_res.url in film_data["characters"]