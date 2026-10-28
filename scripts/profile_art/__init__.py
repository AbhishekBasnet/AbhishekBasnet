"""Artwork for the GitHub profile README.

    config     every tunable value: canvas, palette, text, landscape, sky rules, timeline
    models     plain data types: Cloud, Star, Meteor, Sky
    geometry   box and distance helpers
    sky        rolls the day's sky from a seed (the only module that uses randomness)
    render     turns a Sky into SVG markup (no randomness, no file access)
"""
