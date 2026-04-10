import math
import random

from clues import (
    AdjacencyClue,
    AttributeRelationClue,
    DirectClue,
    gen_adjacency_clues,
    gen_attribute_relation_clues,
    gen_direct_clues,
)

# ---------------------------------------------------------------------------
# Attribute vocabulary (25 categories × 25 values each)
# ---------------------------------------------------------------------------

VOCABULARY = {
    "Name": [
        "Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry",
        "Iris", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Peter",
        "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander", "Yara",
    ],
    "Job": [
        "Doctor", "Farmer", "Pilot", "Engineer", "Teacher", "Lawyer", "Chef",
        "Artist", "Nurse", "Architect", "Scientist", "Writer", "Plumber",
        "Dentist", "Firefighter", "Programmer", "Accountant", "Librarian",
        "Mechanic", "Photographer", "Journalist", "Economist", "Biologist",
        "Chemist", "Physicist",
    ],
    "Color": [
        "Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink",
        "Brown", "Black", "White", "Gray", "Cyan", "Magenta", "Lime",
        "Indigo", "Violet", "Teal", "Maroon", "Navy", "Olive",
        "Coral", "Salmon", "Turquoise", "Gold", "Silver",
    ],
    "Hobby": [
        "Reading", "Gardening", "Cooking", "Painting", "Hiking", "Gaming",
        "Knitting", "Cycling", "Swimming", "Photography", "Sculpting",
        "Dancing", "Singing", "Fishing", "Woodworking", "Yoga", "Chess",
        "Origami", "Birdwatching", "Astronomy", "Archery", "Pottery",
        "Surfing", "Skydiving", "Beekeeping",
    ],
    "Pet": [
        "Dog", "Cat", "Fish", "Bird", "Rabbit", "Hamster", "Turtle",
        "Snake", "Lizard", "Parrot", "Goldfish", "Guinea Pig", "Ferret",
        "Hedgehog", "Chinchilla", "Iguana", "Tarantula", "Frog", "Axolotl",
        "Gecko", "Cockatiel", "Bearded Dragon", "Chameleon", "Tortoise", "Koi",
    ],
    "Nationality": [
        "American", "British", "French", "German", "Japanese", "Chinese",
        "Brazilian", "Australian", "Canadian", "Italian", "Spanish",
        "Mexican", "Indian", "Russian", "Swedish", "Norwegian", "Dutch",
        "Swiss", "Argentine", "Korean", "Turkish", "Egyptian", "Nigerian",
        "South African", "Thai",
    ],
    "Drink": [
        "Coffee", "Tea", "Water", "Juice", "Milk", "Beer", "Wine",
        "Lemonade", "Cola", "Soda", "Smoothie", "Cider", "Kombucha",
        "Espresso", "Cappuccino", "Hot Chocolate", "Iced Tea", "Sparkling Water",
        "Ginger Beer", "Tonic Water", "Matcha", "Chai", "Hibiscus Tea",
        "Coconut Water", "Horchata",
    ],
    "Sport": [
        "Soccer", "Basketball", "Tennis", "Baseball", "Hockey", "Golf",
        "Volleyball", "Rugby", "Cricket", "Badminton", "Table Tennis",
        "Swimming", "Running", "Cycling", "Boxing", "Wrestling",
        "Archery", "Fencing", "Rowing", "Skiing", "Snowboarding",
        "Surfing", "Climbing", "Judo", "Karate",
    ],
    "Music": [
        "Rock", "Jazz", "Classical", "Pop", "Hip-Hop", "Country",
        "Blues", "R&B", "Electronic", "Reggae", "Metal", "Folk",
        "Punk", "Indie", "Soul", "Funk", "Gospel", "Latin",
        "K-Pop", "Opera", "Ambient", "Bluegrass", "Ska", "Disco", "Techno",
    ],
    "Car": [
        "Toyota", "Honda", "Ford", "BMW", "Mercedes", "Tesla", "Audi",
        "Volkswagen", "Chevrolet", "Nissan", "Hyundai", "Kia", "Subaru",
        "Mazda", "Volvo", "Jeep", "Porsche", "Ferrari", "Lamborghini",
        "Bentley", "Dodge", "Chrysler", "Jaguar", "Land Rover", "Lexus",
    ],
    "Food": [
        "Pizza", "Sushi", "Pasta", "Burger", "Tacos", "Salad", "Curry",
        "Steak", "Ramen", "Paella", "Dim Sum", "Pho", "Gyoza", "Falafel",
        "Burritos", "Pad Thai", "Biryani", "Risotto", "Moussaka", "Tagine",
        "Pierogi", "Baklava", "Empanadas", "Jollof Rice", "Ceviche",
    ],
    "Book": [
        "Mystery", "Romance", "Sci-Fi", "Fantasy", "Thriller", "Biography",
        "History", "Self-Help", "Horror", "Comedy", "Drama", "Adventure",
        "Poetry", "Philosophy", "Science", "Travel", "Cookbook", "Children",
        "Graphic Novel", "Memoir", "Politics", "Psychology", "Economics",
        "Mythology", "Anthology",
    ],
    "Language": [
        "English", "Spanish", "French", "German", "Japanese", "Mandarin",
        "Arabic", "Portuguese", "Russian", "Italian", "Korean", "Hindi",
        "Dutch", "Swedish", "Polish", "Turkish", "Greek", "Hebrew",
        "Thai", "Vietnamese", "Indonesian", "Swahili", "Farsi", "Urdu", "Bengali",
    ],
    "Planet": [
        "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn",
        "Uranus", "Neptune", "Pluto", "Eris", "Haumea", "Makemake",
        "Ceres", "Ganymede", "Titan", "Europa", "Callisto", "Io",
        "Triton", "Charon", "Oberon", "Titania", "Ariel", "Umbriel", "Miranda",
    ],
    "Flower": [
        "Rose", "Tulip", "Daisy", "Orchid", "Sunflower", "Lily", "Lavender",
        "Jasmine", "Peony", "Iris", "Marigold", "Daffodil", "Chrysanthemum",
        "Carnation", "Zinnia", "Dahlia", "Poppy", "Lotus", "Magnolia",
        "Hibiscus", "Begonia", "Camellia", "Gardenia", "Freesia", "Aster",
    ],
    "Tree": [
        "Oak", "Maple", "Pine", "Birch", "Cedar", "Willow", "Cherry",
        "Elm", "Ash", "Beech", "Walnut", "Chestnut", "Redwood", "Sequoia",
        "Bamboo", "Palm", "Cypress", "Spruce", "Fir", "Juniper",
        "Acacia", "Baobab", "Eucalyptus", "Magnolia", "Sycamore",
    ],
    "Element": [
        "Hydrogen", "Helium", "Carbon", "Nitrogen", "Oxygen", "Sodium",
        "Magnesium", "Aluminum", "Silicon", "Sulfur", "Chlorine", "Potassium",
        "Calcium", "Iron", "Copper", "Zinc", "Silver", "Gold", "Mercury",
        "Lead", "Uranium", "Titanium", "Nickel", "Cobalt", "Chromium",
    ],
    "Gemstone": [
        "Diamond", "Ruby", "Emerald", "Sapphire", "Amethyst", "Topaz",
        "Opal", "Pearl", "Garnet", "Turquoise", "Aquamarine", "Citrine",
        "Onyx", "Jade", "Amber", "Coral", "Lapis Lazuli", "Moonstone",
        "Peridot", "Tanzanite", "Spinel", "Alexandrite", "Tourmaline",
        "Zircon", "Iolite",
    ],
    "Instrument": [
        "Piano", "Guitar", "Violin", "Drums", "Flute", "Cello", "Trumpet",
        "Saxophone", "Clarinet", "Harp", "Oboe", "Trombone", "Tuba",
        "Mandolin", "Banjo", "Ukulele", "Accordion", "Bass Guitar",
        "French Horn", "Piccolo", "Bassoon", "Xylophone", "Marimba",
        "Sitar", "Didgeridoo",
    ],
    "Country": [
        "USA", "UK", "France", "Germany", "Japan", "China", "Brazil",
        "Australia", "Canada", "Italy", "Spain", "Mexico", "India",
        "Russia", "Sweden", "Norway", "Netherlands", "Switzerland",
        "Argentina", "South Korea", "Turkey", "Egypt", "Nigeria",
        "South Africa", "Thailand",
    ],
    "Animal": [
        "Lion", "Tiger", "Elephant", "Giraffe", "Zebra", "Penguin",
        "Dolphin", "Eagle", "Wolf", "Bear", "Fox", "Deer", "Kangaroo",
        "Koala", "Panda", "Cheetah", "Gorilla", "Chimpanzee", "Jaguar",
        "Leopard", "Rhinoceros", "Hippopotamus", "Crocodile", "Falcon", "Owl",
    ],
    "Mineral": [
        "Quartz", "Feldspar", "Mica", "Calcite", "Pyrite", "Halite",
        "Gypsum", "Magnetite", "Hematite", "Obsidian", "Granite", "Basalt",
        "Marble", "Slate", "Sandstone", "Limestone", "Dolomite", "Fluorite",
        "Apatite", "Talc", "Corundum", "Barite", "Galena", "Sphalerite", "Cinnabar",
    ],
    "Myth": [
        "Zeus", "Apollo", "Athena", "Hermes", "Poseidon", "Artemis",
        "Ares", "Hephaestus", "Aphrodite", "Demeter", "Dionysus", "Hera",
        "Odin", "Thor", "Loki", "Freya", "Ra", "Osiris", "Isis",
        "Anubis", "Vishnu", "Shiva", "Brahma", "Ganesha", "Lakshmi",
    ],
    "Season": [
        "Spring", "Summer", "Autumn", "Winter",
        "Early Spring", "Late Spring", "Early Summer", "Late Summer",
        "Early Autumn", "Late Autumn", "Early Winter", "Late Winter",
        "Monsoon", "Dry Season", "Wet Season", "Harvest Season",
        "Planting Season", "Rainy Season", "Snow Season", "Bloom Season",
        "Storm Season", "Fog Season", "Heat Wave", "Cold Snap", "Thaw Season",
    ],
    "Gemstone2": [
        "Alexandrite2", "Ametrine", "Andalusite", "Apatite2", "Aragonite",
        "Azurite", "Beryl", "Bixbite", "Brazilianite", "Chrysoberyl",
        "Chrysoprase", "Cordierite", "Danburite", "Demantoid", "Diopside",
        "Dioptase", "Enstatite", "Epidote", "Euclase", "Fayalite",
        "Fluorite2", "Goshenite", "Heliodor", "Hemimorphite", "Hiddenite",
    ],
}

ATTR_NAMES = list(VOCABULARY.keys())


# ---------------------------------------------------------------------------
# Solution generation
# ---------------------------------------------------------------------------

def _generate_solution(num_people: int, num_attrs: int) -> list[dict]:
    chosen_attrs = random.sample(ATTR_NAMES, num_attrs)
    solution = [{"Position": i} for i in range(num_people)]
    for attr in chosen_attrs:
        values = random.sample(VOCABULARY[attr], num_people)
        for i, person in enumerate(solution):
            person[attr] = values[i]
    return solution


def _weighted_shuffle(
    direct: list, relation: list, adjacency: list, rng: random.Random
) -> list:
    """Interleave three clue lists with probabilities proportional to their sizes."""
    pools = [list(d) for d in (direct, relation, adjacency)]
    for pool in pools:
        rng.shuffle(pool)
    result = []
    while any(pools):
        weights = [len(p) for p in pools]
        total = sum(weights)
        r = rng.random() * total
        cumulative = 0.0
        chosen = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r < cumulative:
                chosen = i
                break
        result.append(pools[chosen].pop())
    return result


def _clue_count_threshold(num_people: int, num_attrs: int) -> int:
    """Compute the minimum number of clues needed to uniquely determine a puzzle.

    Uses the information-theoretic lower bound: num_attrs * log2(num_people!)
    combined with a floor of num_people * (num_attrs + 1).
    """
    info_bits = num_attrs * math.log2(math.factorial(num_people))
    return max(num_people * (num_attrs + 1), math.ceil(info_bits) + num_people)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_puzzle(num_people: int, num_attrs: int) -> dict:
    rng = random.Random()
    solution = _generate_solution(num_people, num_attrs)

    direct_clues = gen_direct_clues(solution)
    relation_clues = gen_attribute_relation_clues(solution)
    adjacency_clues = gen_adjacency_clues(solution)
    all_clues = _weighted_shuffle(direct_clues, relation_clues, adjacency_clues, rng)

    k = _clue_count_threshold(num_people, num_attrs)
    chosen = all_clues[:k]

    return {"solution": solution, "clues": chosen, "num_clues": len(chosen)}
