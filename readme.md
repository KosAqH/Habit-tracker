# Habit-tracker

Habit and mood tracking application, that let's user also wrote his journal. It is developed as my Flask learning project.

Python ver. 3.10.7

Used CSS framework Bulma: https://bulma.io/

### Instruction

Clone this repo

```
git clone https://github.com/KosAqH/Habit-tracker.git
cd Habit-tracker
```

Create venv and install required packages. 

```
python -m venv venv
.\venv\Scripts\activate
pip install -r .\requirements.txt
```

>[!WARNING]
>Be sure to install matplotlib in version older than 3.6. Since this version July package build on top of matplotlib (that I use for generating calendar-like heatmaps) doesn't work properly.

Run it!

```
python .\run.py
```

### Functionality

Already done:
 - Habit and mood tracking.
 - Views for exploring history of user's entries.
 - Visualization of consistency of getting habits done.
 - Simple users account system, made with Flask-login
 - Functions and classes are documentated

Things to do:
 - Refactor application, in way that testing will be easier (eg. modify app to use flask app factory design pattern, modify some functions that they can be tested in isolation from entire app)
 - Extend test coverage
 - Create more advanced managing habits system (eg. possiblity of exploring data from turned off habits)
 - Allow user to export their data.
 - Create more visualizations and ways of exploring data


### Showcase



https://github.com/KosAqH/Habit-tracker/assets/82679650/cc23d32f-16b6-4d2b-b2c1-119bfbc36599

