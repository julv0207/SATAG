window.SATAG_SAMPLES = {
  "figure": [
    {
      "id": "fig1-keyboard-bird-0",
      "panel": "a",
      "pair": "keyboard-bird",
      "method": "DegDiT",
      "overlap": 0,
      "events": [
        {
          "name": "Keyboard Typing",
          "start": 0.73,
          "end": 4.31
        },
        {
          "name": "Bird Chirping",
          "start": 5.77,
          "end": 9.35
        }
      ],
      "duration": 10,
      "audio": "assets/fig1-keyboard-bird-0.mp3",
      "image": "assets/fig1-keyboard-bird-0.png",
      "imageCrop": {
        "top": 95,
        "width": 1420,
        "height": 603
      }
    },
    {
      "id": "fig1-speech-cat-0",
      "panel": "b",
      "pair": "speech-cat",
      "method": "DegDiT",
      "overlap": 0,
      "events": [
        {
          "name": "Man Talking",
          "start": 0.73,
          "end": 4.31
        },
        {
          "name": "Cat Meowing",
          "start": 5.77,
          "end": 9.35
        }
      ],
      "duration": 10,
      "audio": "assets/fig1-speech-cat-0.mp3",
      "image": "assets/fig1-speech-cat-0.png",
      "imageCrop": {
        "top": 95,
        "width": 1420,
        "height": 603
      }
    },
    {
      "id": "fig1-keyboard-bird-50",
      "panel": "c",
      "pair": "keyboard-bird",
      "method": "DegDiT",
      "overlap": 50,
      "events": [
        {
          "name": "Keyboard Typing",
          "start": 1.31,
          "end": 5.87
        },
        {
          "name": "Bird Chirping",
          "start": 3.59,
          "end": 8.15
        }
      ],
      "duration": 10,
      "audio": "assets/fig1-keyboard-bird-50.mp3",
      "image": "assets/fig1-keyboard-bird-50.png",
      "imageCrop": {
        "top": 95,
        "width": 1420,
        "height": 603
      }
    },
    {
      "id": "fig1-speech-cat-100",
      "panel": "d",
      "pair": "speech-cat",
      "method": "DegDiT",
      "overlap": 100,
      "events": [
        {
          "name": "Man Talking",
          "start": 2.24,
          "end": 6.97
        },
        {
          "name": "Cat Meowing",
          "start": 2.24,
          "end": 6.97
        }
      ],
      "duration": 10,
      "audio": "assets/fig1-speech-cat-100.mp3",
      "image": "assets/fig1-speech-cat-100.png",
      "imageCrop": {
        "top": 95,
        "width": 1420,
        "height": 603
      }
    },
    {
      "id": "fig1-keyboard-bird-satag-50",
      "panel": "e",
      "pair": "keyboard-bird",
      "method": "SATAG",
      "overlap": 50,
      "events": [
        {
          "name": "Keyboard Typing",
          "start": 1.31,
          "end": 5.87
        },
        {
          "name": "Bird Chirping",
          "start": 3.59,
          "end": 8.15
        }
      ],
      "duration": 10,
      "audio": "assets/fig1-keyboard-bird-satag-50.mp3",
      "image": "assets/fig1-keyboard-bird-satag-50.png",
      "imageCrop": {
        "top": 95,
        "width": 1420,
        "height": 603
      }
    },
    {
      "id": "fig1-speech-cat-satag-100",
      "panel": "f",
      "pair": "speech-cat",
      "method": "SATAG",
      "overlap": 100,
      "events": [
        {
          "name": "Man Talking",
          "start": 2.24,
          "end": 6.97
        },
        {
          "name": "Cat Meowing",
          "start": 2.24,
          "end": 6.97
        }
      ],
      "duration": 10,
      "audio": "assets/fig1-speech-cat-satag-100.mp3",
      "image": "assets/fig1-speech-cat-satag-100.png",
      "imageCrop": {
        "top": 95,
        "width": 1420,
        "height": 603
      }
    }
  ],
  "dataset": [
    {
      "id": "4YMXgLFcR94",
      "duration": 10,
      "caption": "A man speaks, and an audience applauds",
      "spot_caption": "Man Speaking from 1.004 to 6.331 and Applause from 6.811 to 10.0",
      "events": [
        {
          "name": "Man Speaking",
          "intervals": [
            [
              1.0,
              6.33
            ]
          ]
        },
        {
          "name": "Applause",
          "intervals": [
            [
              6.81,
              10.0
            ]
          ]
        }
      ],
      "audio": "assets/audiocaps-t-4YMXgLFcR94.mp3"
    },
    {
      "id": "BMayJId0X1s",
      "duration": 10,
      "caption": "A baby crying and a man speaking",
      "spot_caption": "Man Speaking from 2.56 to 3.621 and Man Speaking from 4.431 to 7.401 and Man Speaking from 8.518 to 10.0 and Baby Crying from 0.134 to 2.5 and Baby Crying from 3.204 to 8.508 and Baby Crying from 9.28 to 10.0",
      "events": [
        {
          "name": "Man Speaking",
          "intervals": [
            [
              2.56,
              3.62
            ],
            [
              4.43,
              7.4
            ],
            [
              8.52,
              10.0
            ]
          ]
        },
        {
          "name": "Baby Crying",
          "intervals": [
            [
              0.13,
              2.5
            ],
            [
              3.2,
              8.51
            ],
            [
              9.28,
              10.0
            ]
          ]
        }
      ],
      "audio": "assets/audiocaps-t-BMayJId0X1s.mp3"
    },
    {
      "id": "c6YJgZ3qzOw",
      "duration": 10,
      "caption": "High frequency humming and vibrations",
      "spot_caption": "Motor Running from 0.0 to 6.34 and Whirring from 0.0 to 5.371 and Motor Stopping from 5.671 to 6.34 and Whoosh from 0.0 to 5.371",
      "events": [
        {
          "name": "Motor Running",
          "intervals": [
            [
              0.0,
              6.34
            ]
          ]
        },
        {
          "name": "Whirring",
          "intervals": [
            [
              0.0,
              5.37
            ]
          ]
        },
        {
          "name": "Motor Stopping",
          "intervals": [
            [
              5.67,
              6.34
            ]
          ]
        },
        {
          "name": "Whoosh",
          "intervals": [
            [
              0.0,
              5.37
            ]
          ]
        }
      ],
      "audio": "assets/audiocaps-t-c6YJgZ3qzOw.mp3"
    }
  ],
  "comparisons": [
    {
      "id": "baseline-keyboard-bird-0",
      "pair": "keyboard-bird",
      "overlap": 0,
      "events": [
        {
          "name": "Keyboard Typing",
          "start": 0.73,
          "end": 4.31
        },
        {
          "name": "Bird Chirping",
          "start": 5.77,
          "end": 9.35
        }
      ],
      "duration": 10,
      "baseline": {
        "audio": "assets/baseline-keyboard-bird-0.mp3",
        "image": "assets/baseline-keyboard-bird-0.png"
      },
      "satag": null
    },
    {
      "id": "baseline-keyboard-bird-50",
      "pair": "keyboard-bird",
      "overlap": 50,
      "events": [
        {
          "name": "Keyboard Typing",
          "start": 1.31,
          "end": 5.87
        },
        {
          "name": "Bird Chirping",
          "start": 3.59,
          "end": 8.15
        }
      ],
      "duration": 10,
      "baseline": {
        "audio": "assets/baseline-keyboard-bird-50.mp3",
        "image": "assets/baseline-keyboard-bird-50.png"
      },
      "satag": null
    },
    {
      "id": "baseline-keyboard-bird-100",
      "pair": "keyboard-bird",
      "overlap": 100,
      "events": [
        {
          "name": "Keyboard Typing",
          "start": 2.24,
          "end": 6.97
        },
        {
          "name": "Bird Chirping",
          "start": 2.24,
          "end": 6.97
        }
      ],
      "duration": 10,
      "baseline": {
        "audio": "assets/baseline-keyboard-bird-100.mp3",
        "image": "assets/baseline-keyboard-bird-100.png"
      },
      "satag": null
    },
    {
      "id": "baseline-speech-cat-0",
      "pair": "speech-cat",
      "overlap": 0,
      "events": [
        {
          "name": "Man Talking",
          "start": 0.73,
          "end": 4.31
        },
        {
          "name": "Cat Meowing",
          "start": 5.77,
          "end": 9.35
        }
      ],
      "duration": 10,
      "baseline": {
        "audio": "assets/baseline-speech-cat-0.mp3",
        "image": "assets/baseline-speech-cat-0.png"
      },
      "satag": null
    },
    {
      "id": "baseline-speech-cat-50",
      "pair": "speech-cat",
      "overlap": 50,
      "events": [
        {
          "name": "Man Talking",
          "start": 1.31,
          "end": 5.87
        },
        {
          "name": "Cat Meowing",
          "start": 3.59,
          "end": 8.15
        }
      ],
      "duration": 10,
      "baseline": {
        "audio": "assets/baseline-speech-cat-50.mp3",
        "image": "assets/baseline-speech-cat-50.png"
      },
      "satag": null
    },
    {
      "id": "baseline-speech-cat-100",
      "pair": "speech-cat",
      "overlap": 100,
      "events": [
        {
          "name": "Man Talking",
          "start": 2.24,
          "end": 6.97
        },
        {
          "name": "Cat Meowing",
          "start": 2.24,
          "end": 6.97
        }
      ],
      "duration": 10,
      "baseline": {
        "audio": "assets/baseline-speech-cat-100.mp3",
        "image": "assets/baseline-speech-cat-100.png"
      },
      "satag": null
    }
  ],
  "mixing": [
    {
      "id": "mixing-pair-1",
      "main": "Dog Barking",
      "background": "Bird Chirping",
      "inference_time": "2.926s",
      "seed": 42,
      "start": 2.24,
      "end": 6.97,
      "variants": [
        {
          "label": "Raw summation",
          "description": "Source summation without peak normalization",
          "weights": null,
          "peak": 1.202,
          "audio": "assets/mixing-pair-1-variant-1.mp3",
          "image": "assets/mixing-pair-1-variant-1.png"
        },
        {
          "label": "Main 7 : Background 3",
          "description": "Source peak normalization followed by 7:3 weighting",
          "weights": [
            7,
            3
          ],
          "peak": 1.0,
          "audio": "assets/mixing-pair-1-variant-2.mp3",
          "image": "assets/mixing-pair-1-variant-2.png"
        },
        {
          "label": "Main 3 : Background 7",
          "description": "Source peak normalization followed by 3:7 weighting",
          "weights": [
            3,
            7
          ],
          "peak": 1.0,
          "audio": "assets/mixing-pair-1-variant-3.mp3",
          "image": "assets/mixing-pair-1-variant-3.png"
        }
      ]
    },
    {
      "id": "mixing-pair-2",
      "main": "Car Horn Honking",
      "background": "Waves Crashing",
      "inference_time": "2.945s",
      "seed": 42,
      "start": 2.24,
      "end": 6.97,
      "variants": [
        {
          "label": "Raw summation",
          "description": "Source summation without peak normalization",
          "weights": null,
          "peak": 1.191,
          "audio": "assets/mixing-pair-2-variant-1.mp3",
          "image": "assets/mixing-pair-2-variant-1.png"
        },
        {
          "label": "Main 7 : Background 3",
          "description": "Source peak normalization followed by 7:3 weighting",
          "weights": [
            7,
            3
          ],
          "peak": 1.0,
          "audio": "assets/mixing-pair-2-variant-2.mp3",
          "image": "assets/mixing-pair-2-variant-2.png"
        },
        {
          "label": "Main 3 : Background 7",
          "description": "Source peak normalization followed by 3:7 weighting",
          "weights": [
            3,
            7
          ],
          "peak": 1.0,
          "audio": "assets/mixing-pair-2-variant-3.mp3",
          "image": "assets/mixing-pair-2-variant-3.png"
        }
      ]
    }
  ]
};
