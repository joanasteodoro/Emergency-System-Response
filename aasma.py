import networkx as nx 
import matplotlib.pyplot as plt
import click as click
import math
import agent_system as agent
import graphs as graphs
import numpy as np

@click.command()
@click.option('--exec-type', type=click.Choice(['Simulation','Execution'],case_sensitive=False), prompt='Program Mode',help='Program modes')
@click.option('--visualization', type=click.Choice(['On','Off'],case_sensitive=False), prompt='Visualization',help='Visualization of the System')
@click.option('--agent-behaviour', type=click.Choice(['Idle','Patrol','Station','Mix'],case_sensitive=False), prompt='Agent Behaviour',help='Behaviour of Emergency Agents')
def aasma(exec_type, visualization, agent_behaviour):
    """A Multi-Agent resource management program. It has two distinct program modes:\n
    \tSimulation: A list of fixed scenarios where the program will simulate its functionality according
    to distinct probablistic distributions of emergencies (uniform, normal, linear, exponential) and different agent behaviours, for 100 program cycles\n
    \t(Agent Behaviour: Idle=will remain in the same location until asked to move, Patrol=patrols locations when not solving an emergency, Station=returns to station location after solving an emergency, Mix=random choice between idle, patrol and station)\n
    \tExecution: A custom scenario where the user can define Graph node size, number of resources,
    number of emergencies and the number of program cycles\n""" 
    
    user_input(exec_type, visualization, agent_behaviour, None)

def user_input(exec_type, visualization, agent_behaviour, emergency_evaluation):
    graph = None
    node_size = 0
    resources = 0
    emergencies = 0
    cycles = 0

    if(exec_type =="Simulation"):
        options = ['Uniform', 'Normal', 'Linear', 'Exponential']
        distribution = click.prompt('Choose the distribution of emergencies throughout the program\n[Uniform, Normal, Linear, Exponential]')

        while distribution not in options:
            distribution = click.prompt('Invalid input\n. Choose the distribution of emergencies throughout the program\n[Uniform, Normal, Linear, Exponential]')

        graph = graphs.Graph(visualization)
        result = []

        if distribution == 'Uniform':
            result = graph.initial_setup_simulation(distribution)
        elif distribution == 'Normal':
            result = graph.initial_setup_simulation(distribution)
        elif distribution == 'Linear':
            result = graph.initial_setup_simulation(distribution)
        elif distribution == 'Exponential':
            result = graph.initial_setup_simulation(distribution)

        resources = result[0]
        emergencies = result[1]
        cycles = result[2]
        node_size = result[3]

        print("\nYour chosen simulation will have parameters:\n")
        print("Graph node size: " + str(node_size))
        print("Number of resources: " + str(resources))
        print("Number of emergencies: " + str(emergencies))
        print("Program cycles: " + str(cycles))

    elif(exec_type == "Execution"):
        node_size = click.prompt('Choose the Graphs node size', type=int)
        while node_size <= 0:
            node_size = click.prompt('Not a positive Integer. Choose the Graphs node size', type=int)

        resources = click.prompt('Number of resources', type=int)
        while resources <= 0:
            resources = click.prompt('Not a positive Integer. Number of resources', type=int)
        
        emergencies = click.prompt('Number of emergencies', type=int)
        while emergencies <= 0:
            emergencies = click.prompt('Not a positive Integer. Number of emergencies', type=int)
        
        cycles = click.prompt('Program cycles', type=int)
        while cycles <= 0:
            cycles = click.prompt('Not a positive Integer. Program cycles', type=int)

        distribution = "Uniform"
        
        root = math.floor(math.sqrt(node_size))
        graph = graphs.Graph(visualization)
        graph.initial_setup(emergencies,cycles)
        graph.generate_grid_graph(root,root)

    print("\nWelcome to our emergency resource management Multi-Agent system. You have chosen "+exec_type+" mode.")

    city_agent = agent.City_Agent()
    city_agent.initial_setup(graph, resources, agent_behaviour)
    graph.city_agent = city_agent

    graph.exec_type = exec_type
    graph.behaviour = agent_behaviour
    graph.distribution = distribution

    Loop(graph, resources, emergencies, cycles, city_agent, emergency_evaluation)

def Loop(graph, resources, emergencies, cycles, city_agent, emergency_evaluation):
    cycle_count = 0
    graph.visualize_graph()

    if emergency_evaluation != None:
        city_agent.emergency_evaluation = emergency_evaluation
    
    while cycle_count <= cycles or len(city_agent.active_emergencies) > 0:
        graph.cycle_passed(cycle_count)
        cycle_count += 1

        for agent in city_agent.resource_agents_list:
            city_agent.resource_agents_list[agent].move_agent()

    graph.end_visualize_graph()

    print("\nProgram completed. Presenting statistics:\n")
    print("Number of cycles to effectively answer all emergencies: " + str(cycle_count))
    print("Percentage of emergencies succesfully responded to: ")
    response_success = city_agent.calculate_response_success()
    print("   All types: " + str(round(response_success[0],3)) + " %")
    for i in range(1, 6):
         print("   Type " + str(i) + ": " + str(round(response_success[i],3)) + " %")
    print("Final result of Reinforcement Learning in resource distribution: ")
    emergency_evaluation = city_agent.emergency_evaluation
    for i in range(1, 6):
         print("   Type " + str(i) + ": " + str(emergency_evaluation[i]))
    if click.confirm('Do you want to exit program?'):
        click.echo("Thank you for using our program. Until next time!")
        return
    else:
        options = ['Execution', 'Simulation']
        visualization_options = ['On', 'Off']
        behaviour_options = ['Idle', 'Patrol', 'Station', 'Mix']

        exec_mode = click.prompt('\nStarting new program execution. Choose mode to start new program\n[Simulation, Execution]')
        while exec_mode not in options:
            exec_mode = click.prompt('Invalid input.\n Choose mode to start new program\n[Simulation, Execution]')

        visualization = click.prompt('\nVisualization of the System\n[On, Off]')
        while visualization not in visualization_options:
            visualization = click.prompt('Invalid input.\n Visualization of the System\n[On, Off]')

        behaviour = click.prompt('\nAgent Behaviour\n[Idle, Patrol, Station, Mix]')
        while behaviour not in behaviour_options:
            behaviour = click.prompt('Invalid input.\nAgent Behaviour\n[Idle, Patrol, Station, Mix]')

        user_input(exec_mode, visualization, behaviour, emergency_evaluation)

def debug_log(city_agent):
    city_agent.debug_log()
    for agent in city_agent.resource_agents_list:
        city_agent.resource_agents_list[agent].debug_log()
        print("\n")

if __name__ == "__main__":
    aasma(None, None, None)