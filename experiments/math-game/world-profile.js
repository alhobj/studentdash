/* Authored travel routes and collision rectangles, not syllabus prerequisites. */
window.MATH_GAME_PROFILE.rooms=[
  {
    "id": "number",
    "name": "Number market",
    "short": "Market",
    "theme": "market",
    "palette": {
      "ground": "#384b43",
      "detail": "#769887",
      "path": "#b9a578",
      "roof": "#2d3d41",
      "accent": "#ecd493",
      "window": "#fff1c5",
      "water": "#315b78"
    },
    "exits": {
      "right": "functions",
      "down": "statistics"
    },
    "actors": [
      {
        "id": "building",
        "name": "NIA",
        "x": 570,
        "y": 310
      }
    ],
    "solids": [
      {
        "x": 350,
        "y": 106,
        "w": 260,
        "h": 174
      },
      {
        "x": 70,
        "y": 120,
        "w": 160,
        "h": 90
      },
      {
        "x": 730,
        "y": 120,
        "w": 160,
        "h": 90
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 0,
      "y": 0
    }
  },
  {
    "id": "functions",
    "name": "Function foundry",
    "short": "Foundry",
    "theme": "factory",
    "palette": {
      "ground": "#4b4139",
      "detail": "#967957",
      "path": "#b8a17d",
      "roof": "#2f3545",
      "accent": "#dfb776",
      "window": "#f2dca3",
      "water": "#315b78"
    },
    "exits": {
      "left": "number",
      "right": "geometry",
      "down": "calculus"
    },
    "actors": [
      {
        "id": "building",
        "name": "JUN",
        "x": 570,
        "y": 310
      }
    ],
    "solids": [
      {
        "x": 350,
        "y": 106,
        "w": 260,
        "h": 174
      },
      {
        "x": 90,
        "y": 100,
        "w": 120,
        "h": 140
      },
      {
        "x": 740,
        "y": 100,
        "w": 120,
        "h": 140
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 1,
      "y": 0
    }
  },
  {
    "id": "geometry",
    "name": "Surveyor’s harbour",
    "short": "Harbour",
    "theme": "water",
    "palette": {
      "ground": "#284653",
      "detail": "#648fa6",
      "path": "#b3b8a5",
      "roof": "#263449",
      "accent": "#9ccde0",
      "window": "#d9eff6",
      "water": "#315b78"
    },
    "exits": {
      "left": "functions"
    },
    "actors": [
      {
        "id": "building",
        "name": "MIRA",
        "x": 570,
        "y": 310
      }
    ],
    "solids": [
      {
        "x": 350,
        "y": 106,
        "w": 260,
        "h": 174
      },
      {
        "x": 20,
        "y": 100,
        "w": 300,
        "h": 180
      },
      {
        "x": 640,
        "y": 100,
        "w": 300,
        "h": 180
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 2,
      "y": 0
    }
  },
  {
    "id": "statistics",
    "name": "Data gardens",
    "short": "Gardens",
    "theme": "garden",
    "palette": {
      "ground": "#3f3e55",
      "detail": "#879184",
      "path": "#a7a28d",
      "roof": "#303348",
      "accent": "#c5b3df",
      "window": "#e4eed2",
      "water": "#315b78"
    },
    "exits": {
      "up": "number",
      "right": "calculus"
    },
    "actors": [
      {
        "id": "building",
        "name": "SOL",
        "x": 570,
        "y": 310
      }
    ],
    "solids": [
      {
        "x": 350,
        "y": 106,
        "w": 260,
        "h": 174
      },
      {
        "x": 50,
        "y": 136,
        "w": 40,
        "h": 58
      },
      {
        "x": 50,
        "y": 426,
        "w": 40,
        "h": 58
      },
      {
        "x": 180,
        "y": 136,
        "w": 40,
        "h": 58
      },
      {
        "x": 180,
        "y": 426,
        "w": 40,
        "h": 58
      },
      {
        "x": 700,
        "y": 136,
        "w": 40,
        "h": 58
      },
      {
        "x": 700,
        "y": 426,
        "w": 40,
        "h": 58
      },
      {
        "x": 830,
        "y": 136,
        "w": 40,
        "h": 58
      },
      {
        "x": 830,
        "y": 426,
        "w": 40,
        "h": 58
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 0,
      "y": 1
    }
  },
  {
    "id": "calculus",
    "name": "Change observatory",
    "short": "Observatory",
    "theme": "stars",
    "palette": {
      "ground": "#3d304e",
      "detail": "#8b779b",
      "path": "#9c8c9e",
      "roof": "#272c44",
      "accent": "#e2a9a5",
      "window": "#f0dee0",
      "water": "#315b78"
    },
    "exits": {
      "up": "functions",
      "left": "statistics"
    },
    "actors": [
      {
        "id": "building",
        "name": "KAIA",
        "x": 570,
        "y": 310
      }
    ],
    "solids": [
      {
        "x": 350,
        "y": 106,
        "w": 260,
        "h": 174
      },
      {
        "x": 105,
        "y": 150,
        "w": 90,
        "h": 125
      },
      {
        "x": 755,
        "y": 150,
        "w": 90,
        "h": 125
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 1,
      "y": 1
    }
  }
];
