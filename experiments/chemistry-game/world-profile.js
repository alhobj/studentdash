/* Authored travel routes and collision rectangles, not syllabus prerequisites. */
window.GAME_PROFILE.rooms=[
  {
    "id": "S1",
    "name": "Foundations garden",
    "short": "Garden",
    "theme": "garden",
    "palette": {
      "ground": "#64845b",
      "detail": "#527345",
      "path": "#c6ad7a",
      "roof": "#a46f4d",
      "accent": "#b4d38b",
      "window": "#f1d9a0",
      "water": "#4d8799"
    },
    "exits": {
      "right": "S2",
      "down": "R1"
    },
    "actors": [
      {
        "id": "nia",
        "name": "NIA",
        "x": 380,
        "y": 310
      },
      {
        "id": "jun",
        "name": "JUN",
        "x": 580,
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
      "y": 0
    }
  },
  {
    "id": "S2",
    "name": "Materials workshop",
    "short": "Workshop",
    "theme": "factory",
    "palette": {
      "ground": "#7c8661",
      "detail": "#a88d63",
      "path": "#c6ad7a",
      "roof": "#986547",
      "accent": "#dcac6c",
      "window": "#f1d9a0",
      "water": "#4d8799"
    },
    "exits": {
      "left": "S1",
      "right": "S3",
      "down": "R2"
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
    "id": "S3",
    "name": "Pattern archive",
    "short": "Archive",
    "theme": "archive",
    "palette": {
      "ground": "#74816d",
      "detail": "#a6a57b",
      "path": "#c6ad7a",
      "roof": "#7c718a",
      "accent": "#c3a3df",
      "window": "#f1d9a0",
      "water": "#4d8799"
    },
    "exits": {
      "left": "S2",
      "down": "R3"
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
        "x": 65,
        "y": 110,
        "w": 150,
        "h": 48
      },
      {
        "x": 65,
        "y": 180,
        "w": 150,
        "h": 48
      },
      {
        "x": 65,
        "y": 450,
        "w": 150,
        "h": 48
      },
      {
        "x": 735,
        "y": 110,
        "w": 150,
        "h": 48
      },
      {
        "x": 735,
        "y": 180,
        "w": 150,
        "h": 48
      },
      {
        "x": 735,
        "y": 450,
        "w": 150,
        "h": 48
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 2,
      "y": 0
    }
  },
  {
    "id": "R1",
    "name": "Energy station",
    "short": "Energy",
    "theme": "energy",
    "palette": {
      "ground": "#8b865c",
      "detail": "#b99e66",
      "path": "#c6ad7a",
      "roof": "#ac6946",
      "accent": "#f0ad69",
      "window": "#f1d9a0",
      "water": "#4d8799"
    },
    "exits": {
      "up": "S1",
      "right": "R2"
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
        "x": 65,
        "y": 100,
        "w": 150,
        "h": 170
      },
      {
        "x": 740,
        "y": 100,
        "w": 150,
        "h": 170
      }
    ],
    "northExitX": 334,
    "atlas": {
      "x": 0,
      "y": 1
    }
  },
  {
    "id": "R2",
    "name": "Reactor waterworks",
    "short": "Waterworks",
    "theme": "water",
    "palette": {
      "ground": "#689484",
      "detail": "#9db78c",
      "path": "#c6ad7a",
      "roof": "#5e8993",
      "accent": "#8cc9d8",
      "window": "#f1d9a0",
      "water": "#4d8799"
    },
    "exits": {
      "up": "S2",
      "left": "R1",
      "right": "R3"
    },
    "actors": [
      {
        "id": "building",
        "name": "BO",
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
      "x": 1,
      "y": 1
    }
  },
  {
    "id": "R3",
    "name": "Transfer observatory",
    "short": "Observatory",
    "theme": "stars",
    "palette": {
      "ground": "#657486",
      "detail": "#9b9eaf",
      "path": "#c6ad7a",
      "roof": "#68718f",
      "accent": "#e5aec8",
      "window": "#f1d9a0",
      "water": "#4d8799"
    },
    "exits": {
      "up": "S3",
      "left": "R2"
    },
    "actors": [
      {
        "id": "building",
        "name": "BO",
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
      "x": 2,
      "y": 1
    }
  }
];
