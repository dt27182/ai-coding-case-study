"""
Category Data for Logic Puzzle Generation
Contains predefined category names and value pools for puzzle attributes.
"""

from typing import Dict, List


# Predefined category names (ordered by preference)
CATEGORY_NAMES = [
    "name", "color", "pet", "drink", "country", "hobby", "car", "food",
    "sport", "instrument", "season", "weather", "city", "job", "fruit",
    "flower", "book", "movie", "language", "gem"
]


# Value pools for each category
VALUE_POOLS: Dict[str, List[str]] = {
    "name": [
        "Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah",
        "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nancy", "Oliver", "Patricia",
        "Quinn", "Rachel", "Samuel", "Tina"
    ],
    "color": [
        "Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink", "Brown",
        "Black", "White", "Gray", "Cyan", "Magenta", "Violet", "Indigo", "Turquoise",
        "Gold", "Silver", "Maroon", "Navy"
    ],
    "pet": [
        "Dog", "Cat", "Bird", "Fish", "Rabbit", "Hamster", "Turtle", "Snake",
        "Lizard", "Ferret", "Guinea Pig", "Parrot", "Iguana", "Chinchilla", "Hedgehog",
        "Mouse", "Rat", "Frog", "Spider", "Tarantula"
    ],
    "drink": [
        "Coffee", "Tea", "Water", "Juice", "Soda", "Milk", "Wine", "Beer",
        "Smoothie", "Lemonade", "Hot Chocolate", "Energy Drink", "Cocktail", "Whiskey",
        "Vodka", "Rum", "Champagne", "Cider", "Milkshake", "Espresso"
    ],
    "country": [
        "USA", "Canada", "Mexico", "Brazil", "UK", "France", "Germany", "Italy",
        "Spain", "Japan", "China", "India", "Australia", "Russia", "South Africa",
        "Egypt", "Argentina", "Chile", "Sweden", "Thailand"
    ],
    "hobby": [
        "Reading", "Gaming", "Cooking", "Painting", "Photography", "Gardening",
        "Hiking", "Swimming", "Dancing", "Singing", "Writing", "Knitting", "Fishing",
        "Cycling", "Running", "Yoga", "Chess", "Pottery", "Sculpting", "Baking"
    ],
    "car": [
        "Toyota", "Honda", "Ford", "BMW", "Mercedes", "Audi", "Tesla", "Nissan",
        "Chevrolet", "Volkswagen", "Mazda", "Subaru", "Hyundai", "Kia", "Lexus",
        "Porsche", "Ferrari", "Lamborghini", "Jaguar", "Volvo"
    ],
    "food": [
        "Pizza", "Burger", "Pasta", "Sushi", "Tacos", "Steak", "Salad", "Soup",
        "Sandwich", "Rice", "Noodles", "Curry", "Dumplings", "Fries", "Chicken",
        "Fish", "Vegetables", "Fruit", "Bread", "Cheese"
    ],
    "sport": [
        "Soccer", "Basketball", "Tennis", "Baseball", "Football", "Hockey", "Golf",
        "Volleyball", "Swimming", "Running", "Cycling", "Boxing", "Wrestling",
        "Skiing", "Surfing", "Cricket", "Rugby", "Badminton", "Table Tennis", "Archery"
    ],
    "instrument": [
        "Piano", "Guitar", "Violin", "Drums", "Flute", "Trumpet", "Saxophone",
        "Cello", "Clarinet", "Harp", "Trombone", "Oboe", "Bassoon", "Tuba",
        "Ukulele", "Banjo", "Accordion", "Harmonica", "Xylophone", "Marimba"
    ],
    "season": [
        "Spring", "Summer", "Fall", "Winter", "Early Spring", "Late Spring",
        "Early Summer", "Late Summer", "Early Fall", "Late Fall", "Early Winter",
        "Late Winter", "Wet Season", "Dry Season", "Monsoon", "Autumn", "Harvest",
        "Bloom", "Frost", "Thaw"
    ],
    "weather": [
        "Sunny", "Rainy", "Cloudy", "Snowy", "Windy", "Foggy", "Stormy", "Clear",
        "Overcast", "Drizzle", "Sleet", "Hail", "Humid", "Dry", "Hot", "Cold",
        "Mild", "Warm", "Cool", "Freezing"
    ],
    "city": [
        "New York", "Los Angeles", "Chicago", "London", "Paris", "Tokyo", "Berlin",
        "Rome", "Madrid", "Sydney", "Toronto", "Mumbai", "Beijing", "Moscow", "Dubai",
        "Singapore", "Hong Kong", "Seoul", "Bangkok", "Amsterdam"
    ],
    "job": [
        "Doctor", "Teacher", "Engineer", "Lawyer", "Chef", "Artist", "Writer", "Nurse",
        "Programmer", "Designer", "Accountant", "Manager", "Scientist", "Architect",
        "Musician", "Actor", "Pilot", "Mechanic", "Electrician", "Plumber"
    ],
    "fruit": [
        "Apple", "Banana", "Orange", "Grape", "Strawberry", "Blueberry", "Mango",
        "Pineapple", "Watermelon", "Peach", "Pear", "Cherry", "Kiwi", "Plum",
        "Lemon", "Lime", "Raspberry", "Blackberry", "Papaya", "Guava"
    ],
    "flower": [
        "Rose", "Tulip", "Daisy", "Sunflower", "Lily", "Orchid", "Carnation",
        "Daffodil", "Peony", "Iris", "Lavender", "Jasmine", "Hibiscus", "Magnolia",
        "Poppy", "Violet", "Marigold", "Chrysanthemum", "Lotus", "Camellia"
    ],
    "book": [
        "Fiction", "Mystery", "Romance", "Thriller", "Fantasy", "Sci-Fi", "Biography",
        "History", "Poetry", "Drama", "Horror", "Adventure", "Classic", "Contemporary",
        "Crime", "Western", "Memoir", "Cookbook", "Travel", "Self-Help"
    ],
    "movie": [
        "Action", "Comedy", "Drama", "Horror", "Romance", "Thriller", "Sci-Fi",
        "Fantasy", "Animation", "Documentary", "Musical", "Western", "War", "Crime",
        "Mystery", "Adventure", "Biography", "Historical", "Superhero", "Noir"
    ],
    "language": [
        "English", "Spanish", "French", "German", "Chinese", "Japanese", "Korean",
        "Italian", "Portuguese", "Russian", "Arabic", "Hindi", "Dutch", "Swedish",
        "Polish", "Turkish", "Greek", "Hebrew", "Thai", "Vietnamese"
    ],
    "gem": [
        "Diamond", "Ruby", "Sapphire", "Emerald", "Pearl", "Opal", "Topaz", "Amethyst",
        "Garnet", "Aquamarine", "Turquoise", "Jade", "Onyx", "Citrine", "Peridot",
        "Moonstone", "Tanzanite", "Alexandrite", "Tourmaline", "Zircon"
    ]
}
