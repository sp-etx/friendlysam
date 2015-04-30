.. _what-friendly-sam-is-for:

What Friendly Sam is for
================================

Why build another tool?
-------------------------

There are a lot of different tools for optimization-based modeling. Why in the world do we need another one?

The short answer is this: Friendly Sam is a **domain specific toolbox**. For the type of models we work with, the model code is shorter, more readable and easier to debug than it would be with many other tools. Furthermore, Friendly Sam **makes data handling and analysis easier**. Because Friendly Sam is implemented in Python, we get access to all our favorite Python tools for scientific computing and visualization, including Pandas, NumPy, SciPy, matplotlib, etc. This is a strong advantage because the majority of our modeling work is preparing input data and analyzing results.

In the coming paragraphs we'll explain more about what Friendly Sam is. And at end we'll also say a few things Friendly Sam is not.

Data handling is easier with Python
-----------------------------------------------------------

Friendly Sam was designed to simplify our work with optimization-based models of energy systems, so-called *dispatch models*. This is a common type of model in research and in applied analysis of energy systems, based on the thought that the operator(s) of an energy system always act so as to minimize the cost of delivering energy to customers, or maybe (in a parallel universe) to minimize the carbon emissions, or some other objective function. A dispatch model is usually formulated as a minimization problem: *"Minimize the operation cost of this system in this time period, subject to the technical and legal constraints of the system."*

There are a zillion different variants of such models, but many of them have in common that there is a lot of data going in and out. Some examples of possible input data are prices for different forms of energy, demand profiles, technical constraints, etc. The output data could be operation decisions, system costs, greenhouse gas emissions, and many other things. Therefore, a large part of our modeling work is data handling: Reading and wrangling data files, transforming and resampling input and output data, visualizing results, making statistical tests, etc.

Many optimization-based models are implemented using a generic optimization modeling language like GAMS, AMPL, AIMMS or CMPL. These languages can be wonderful to work with when formulating models because they are made specifically for optimization, and they are efficient in transforming your human-readable code into something that can be understood by almost any optimization solver. However, the infrastructure for handling input and output data in GAMS and AMPL is sub-optimal (pun intended). Anyone who implemented a large, complicated model in one of those languages knows it's not an easy ride to keep track of all the data going in and out, especially not if you want to make a lot of similar runs with different parameter sets. I know several people who wrote their own tools for getting inputs and outputs back and forth between GAMS and their favorite data crunching tool (Excel, Python, MATLAB, R, etc).

When we started writing what would later become Friendly Sam, we chose Python because of the great ecosystem of open source tools that come with it. We have paid specific attention to numpy, pandas, and matplotlib when developing Friendly Sam. It's not necessary to use these tools with Friendly Sam, but there is a great chance they will make your life easier. What about optimization then? To formulate and solve the actual optimization problems, we first used the Python API of the Gurobi optimizer. Gurobi's Python API exposes a Variable class with overloaded operators for addition, multiplication, etc, so you can make algebraic expressions for the optimization objective and all the constraints in Python code. The Gurobi backend then translates these expression objects into a well-formed optimization problem, solves the problem and delivers the solution back through the Python API so you never have to leave Python. In Friendly Sam 1.0 we have created an abstraction layer to reduce the dependence on a certain solver backend. We are now using PuLP to interact with the Gurobi and CBC solvers, but you never have to interact directly with the backend, and it is not too hard to switch to another backend if we want to.

Domain specific toolbox
-------------------------------

Friendly Sam is a Python library for formulating, running, and analyzing optimization-based models of energy systems.

In fact, it's not only suitable for modeling energy systems, but also for other systems where you want to optimize flow networks of physical or abstract quantities, be it energy carriers, money, solid waste, cargo deliveries, virtual water or something else.

In principle, you are not even restricted to modeling systems with flow networks, because the optimization engine behind Friendly Sam is exposed so you can formulate a large class of optimization problems. But if you want a generic tool for formulating optimization problems you should probably check out other tools instead. In Python it's worth to look at CyLP, cvxpy, PuLP, and Pyomo. If you want a pure optimization language, look at GAMS, AMPL, AIMMS or CMPL.

So although Friendly Sam can be used as a rather generic optimization modeling tool, it is domain specific in the sense that it has vocabulary for energy systems and similar systems. We developed it specifically to help us formulate dispatch models. In our energy system models, there are almost always balance equations for energy or materials, so Friendly Sam contains definitions of things like ``FlowNetwork``, ``Node`` and ``Cluster`` to simplify the formulation of such constraints. And as you can learn from the :ref:`User Guide <user-guide>`, the ``Node`` class is a perfect starting point for modeling things like power plants, energy storages, and other things you typically find in an energy system. Friendly Sam 1.0 also has a simple formulation of a myopic dispatch model of the type we often encounter in the academic literature on energy system modeling. If you use these building blocks, you will have to think less about sign errors in balance equations and instead concentrate on what your model really means.

Friendly Sam code is meant to be readable. For example, in a district heating model we can have instances of ``Node`` subclasses, one named ``LinearCHP``, another named ``HeatPump``, etc. This makes perfect sense to us, because the code is naturally structured similar to how we think about the energy system we are modeling. When the underlying optimization problem is solved, we can query the state of the model objects with code like ``heat_pump.consumption['power'](time)``.

The code can also be easier to debug. When you have a bewildering error somewhere, it can be helpful to just eyeball the constraints of your optimization problem, to see if you can spot the error. Friendly Sam makes this easier by automatically naming constraints after their "owner", for example the ``HeatPump`` instance we just mentioned. You can also name variables and add descriptions to constraints. These features help you understand where things come from when you are looking at a long list of constraints.

What Friendly Sam is not
---------------------------

First, we want to clarify that Friendly Sam is not "a model". It is a toolbox we use to build models.

Second, Friendly Sam is not fool proof. It is entirely possible to make models that are stupid or wrong with Friendly Sam. We have tried to design Friendly Sam to produce readable, understandable, debuggable models, and to make idioms and conventions that help to avoid common errors. But having this tool is not an alternative to knowing and understanding the optimization problems you are creating. Friendly Sam is a tool to help us focus on what is important, rather than chasing indexing errors and how to formulate piecewise affine functions using special ordered sets.

Third, Friendly Sam is not primarily optimized for speed. If you want to solve a really big model fast, you are probably better off with something like AMPL or GAMS, or maybe writing your own code in a compiled language. However, if your model is moderately big you might get the job done faster with Friendly Sam because debugging, data handling, analysis and visualization will be so much faster. In our experience, the development phase often consumes more time and money than the computation phase, so development convenience is often more important than execution speed.

OK, let's get started!
------------------------

To learn how Friendly Sam works and what sets it apart from other tools, check out the :ref:`User Guide <user-guide>`.
