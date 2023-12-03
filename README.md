# BoomGame

Re-implementation of BOOM game (old macintosh game) with python & pygame.

[BOOM](https://www.macintoshrepository.org/3582-boom) was created by Federico Filipponi (FactorSoftware) in the ’90s. It is an arcade game that can be played by up to two player on a single computer. Players are facing an alien invasion in 80 levels. Their goal is to elimitate all the aliens with their bombs.

The game is not supported any more and can be played only on macos X (> 10 years old). This is a fan remake of BOOM in python using pygame library. This implementation can run on any os/laptop that support python3 and pygame. **NOTE: The original BOOM assets belong to Factor Software. We do not hold any intellectual property upon them.**

This work is still in development. A more mature remake of the game in C++ is available in the [Lifish](https://github.com/silverweed/lifish) project.

## Install
### Download executables

Soon available.

### From pypi
It requires to install python and pip first.

To install the the game (will also install pygame), you can run:

```
$ pip install boomgame
```

Once installed, the game can be launched with

```
$ boom
```

### From source
Download the source code. (Install python, pip and set up python environment)

Run:

```
$ pip install -e .
```

Again, the game can be launched with

```
$ boom
```

## Story
It’s happened again. The Earth is facing a new alien threat and who’s called to save our beloved planet? You guessed!

The aliens have the capability of transform themselves in all sort of deadly creatures. Basically, they act like parasites, attacking humans, animals and even machines and turning them into lethal killers.

Your mission is to penetrate 8 alien infested areas, each one divided in 10 sub-zones, eliminate all enemies using your bombs and finally kick the Big Alien Boss back to where he came from.

## BUGS and missing features

* The final boss is not yet integrated into the game
* The menu is still in beta and the player's controls cannot be changed yet
* Enemies can sometimes be stuck against one another (specially in timeout mode)


## Old BOOM Credits

The game [BOOM](https://www.macintoshrepository.org/3582-boom) has been created by Federico Filipponi.
Copyright 1997-2011 Factor Software. All Rights Reserved.

The sounds and music of BOOM have been created by George E. Kouba, Jr. and are copyrighted by Wizid Multimedia. Used with permission.

BOOM makes use of MGGame, an OpenGL/OpenAL based library suitable for developing 2D games for Mac OS X and iOS (iPhone, iPod Touch, iPad).
MGGame is Copyright © by Sebastian Wegner.
Sebastian is also leading McSebi Software, a team of independent game developers devoted to create fun shareware video games for the Mac and Apple mobiles.

The loading screen artwork has been made by Raymond Zachariasse, a web designer and freelance graphic artist, leader of the Quality Team.

BOOM also makes use of the Tempesta Seven Fonts by Yusuke Kamiyamane.
