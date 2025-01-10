import random


def get_image_description():

    mock_descriptions = [
        "A serene mountain landscape with a clear blue lake reflecting the snowy peaks.",
        "A bustling city street at night, illuminated by neon signs and headlights.",
        "A cozy reading nook with a large armchair, a blanket, and bookshelves filled with books.",
        "A golden sunset over a vast desert, with sand dunes casting long shadows.",
        "A futuristic cityscape with towering skyscrapers and flying vehicles in the sky.",
        "A peaceful forest path surrounded by tall trees with sunlight streaming through the canopy.",
        "A close-up of a tiger prowling through the jungle, its eyes glowing with intensity.",
        "A quaint village nestled in a valley, with stone houses and smoke rising from chimneys.",
        "A vibrant coral reef underwater, teeming with colorful fish and marine life.",
        "An astronaut floating in space, with Earth visible in the background.",
    ]

    return random.choice(mock_descriptions)
