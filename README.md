# chippy
Chip8 emulator in Python made manageable with pseudo functional programming or data-oriented programming. I don't know anymore, I sold my soul to a demon to code in Python

# What is this?
This is my attempt at Chip8 emulator. Emulator is a program, that behaves like a real hardware of some system. It allows us to run binaries that are not native to the system totally okay, since the program doesn't suspect that the underneath it is not a real hardware, but a software emulating it.

Of course, the accuracy of the emulator depends on the quality of the emulator and sometimes it may be timing specific.

# Why
I wanted to write emulators, and I will most certainly continue. But I don't like how even the simplest emulators are overcomplicated for some reason. So I tried to write a simple emulator. And I did it with a help of functional and data-oriented programming.

# How to run
Simply type in terminal:
```
python3 main.py <rom_name>
```

# How to configure
At the moment you can only change the source code. There are `SCALE_FACTOR` which scales the window, and `default_keymap()` function which generates a keymap, which tells the program how to map user input to Chip8 keys.

# Known problems
The emulation is slow, probably due to the fact, that there is a lot of copying that is going on. This is due to the fact that I attempted to write this program in functional style. People say that Python has functional programming capabilities, and I agree. Python is an FP language in the same way the car falling of a cliff is an airplane.

# What is Functional Programming and Data-Oriented Programming
Well, functional programming is a way of programming, where the main unit of programming is a function. But not every function, but a pure function. A pure function is the one, that takes some value, and returns a corresponding value, and nothing else. It also doesn't change the arguments that are given to it, but returns a whole new copy.

In theory, it should produce a simpler, and easier code to read. Please [see for yourself](https://github.com/craigthomas/Chip8Python) which is more readable and understandable to you.

And for the data-oriented programming, it is an approach to programming, where the main focus is data. You work in terms of data and make sure that your functions work on transforming the said data. You decouple the data from the methods of a class, and thus you get back the flexibility that is taken away by the rigidness of OOP.

The thing about Data-Oriented Programming is that it can be applied even in OOP languages, such as Java. If you can't do FP, then do DOP.

I can say even more, that the FP is a better OOP with all of its encapsulation, polimorphism, type-checking, etc than the native OOP languages are. But that is a topic for another day.
