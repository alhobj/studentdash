/* Authored travel routes and collision rectangles, not syllabus prerequisites. */
window.MATH_GAME_PROFILE.rooms=[
  {
    "id": "number",
    "name": "Number market",
    "short": "Market",
    "theme": "market",
    "palette": {
      "ground": "#839363",
      "detail": "#a9b375",
      "path": "#c6ad7a",
      "roof": "#b57b52",
      "accent": "#ecd493",
      "window": "#f1d9a0",
      "water": "#4d8799"
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
      "ground": "#7c8661",
      "detail": "#a88d63",
      "path": "#c6ad7a",
      "roof": "#986547",
      "accent": "#dfb776",
      "window": "#f1d9a0",
      "water": "#4d8799"
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
      "ground": "#689484",
      "detail": "#9db78c",
      "path": "#c6ad7a",
      "roof": "#5e8993",
      "accent": "#9ccde0",
      "window": "#f1d9a0",
      "water": "#4d8799"
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
      "ground": "#64845b",
      "detail": "#527345",
      "path": "#c6ad7a",
      "roof": "#a46f4d",
      "accent": "#c5b3df",
      "window": "#f1d9a0",
      "water": "#4d8799"
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
      "ground": "#657486",
      "detail": "#9b9eaf",
      "path": "#c6ad7a",
      "roof": "#68718f",
      "accent": "#e2a9a5",
      "window": "#f1d9a0",
      "water": "#4d8799"
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
