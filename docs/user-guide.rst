.. _user-guide:

Friendly Sam User Guide
====================================================================================

Introduction: What Friendly Sam is and isn't
-----------------------------------------------

Friendly Sam is a Python library for formulating, running, and analyzing optimization-based models of energy systems.

In fact, it's not only suitable for modeling energy systems, but also for other systems where you want to optimize flow networks of physical or abstract quantities, be it energy carriers, money, solid waste, cargo deliveries, virtual water or something else.

In principle, you are not even restricted to modeling systems with flow networks, because the optimization engine behind Friendly Sam is fully exposed so you can formulate a large class of optimization problems. But if you want a generic tool for formulating optimization problems you should probably check out tools like CyLP, cvxpy, PuLP, Pyomo, GAMS, AMPL or CMPL instead.

So although Friendly Sam can be used as a rather generic optimization modeling tool, it is domain specific in the sense that it's designed for energy systems and similar systems. It was developed to help us formulate so-called *dispatch models* of energy systems, where the operator(s) of the model system run their plants so as to minimize the cost of delivering energy to their customers, or maybe (in a parallel universe) to minimize the carbon emissions, or some other objective function. In our energy system models, there are almost always balance equations for energy or materials, so Friendly Sam contains definitions of things like ``FlowNetwork``, ``Node`` and ``Cluster`` to simplify the formulation of such constraints. As you will see later on, the ``Node`` class is a perfect starting point for modeling things like power plants, energy storages, and other things you typically find in an energy system. Friendly Sam 1.0 also has a simple formulation of a myopic dispatch model of the type we often encounter in the academic literature on energy system modelling. If you use these building blocks, you will have to think less about sign errors in equations and instead concentrate on what your model really means.

A large part of our work with models is in handling the inputs and outputs: Reading and wrangling data files, transforming and resampling input and output data, visualizing results, making statistical tests, etc. Friendly Sam is written in Python because there is a great ecosystem of tools in Python for these tasks. We have paid specific attention to numpy, pandas, and matplotlib when developing Friendly Sam. It's not necessary to use these tools with Friendly Sam, but there is a great chance they will make your life easier.

Friendly Sam is made with debugging in mind. Unless you are Chuck Norris, you probably also make errors in programming or modeling sometimes. When you have a bewildering error somewhere, it can be helpful to just eyeball the constraints of your optimization problem, to see if you can spot the error. Friendly Sam makes this type of debugging easier by letting you name variables and add descriptions to constraints, so you can understand where they come from.

Before we start with the details, we'll mention a few things Friendly Sam is not.

First, Friendly Sam is not "a model". It is more like a toolbox we use to build different models, and it's very extensible and adaptable to whatever needs might come up.

Second, it is not fool proof. It is entirely possible to make models that are stupid or wrong with Friendly Sam. We have tried to design Friendly Sam to produce readable, understandable, debuggable models, and to make idioms and conventions that help to avoid common errors. But having this tool is not an alternative to knowing and understanding the optimization problems you are creating. Friendly Sam is a tool to help us focus on what is important, rather than chasing sign errors and how to formulate piecewise affine functions using special ordered sets.

Third, Friendly Sam is not primarily optimized for speed. If you want to solve a really big model fast, you are probably better off with something like AMPL or GAMS, or even writing your own code. However, if your model is moderately big you might get the job done faster with Friendly Sam because debugging, data handling, analysis and visualization will be so much faster. In our experience, the development phase often consumes more time and money than the computation phase, so development convenience is often more important than execution speed.


Optimization: Variables, constraints, problems, and solvers
---------------------------------------------------------------

Variables are central to any optimization problem. With Friendly Sam, each variable is an instance of the ``Variable`` class. Variables can be added, multiplied, subtracted, and so on, to form expressions, including equalities and inequalities.

::

	>>> import friendlysam as fs
	>>> my_var = fs.Variable('x')
	>>> my_var
	<Variable at 0x...: x>
	>>> my_var * 2 + 1
	<Add at 0x...: x * 2 + 1>
	>>> (my_var + 1) * 2
	<Mul at 0x...: (x + 1) * 2>
	>>> my_var * 2 <= 3
	<LessEqual at 0x...: x * 2 <= 3>
