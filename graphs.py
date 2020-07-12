import numpy as np
import networkx as nx 
import matplotlib.pyplot as plt
from scipy.stats import truncnorm
from scipy.stats import truncexpon
import click as click
import math
import agent_system as agent

def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)

def get_truncated_exponential(lower=0, upper=1000, scale=0.5):
    return truncexpon(b=(upper-lower)/scale, loc=lower, scale=scale)

class GraphNode:

    def __init__(self):

        # Location of node
        self.location = None

        # status of active emergency in location
        self.emergency = None

        # Node color
        self.color = "grey"
        self.color_scale = ["#FCFF33", "#FFDA33", "#FF9F33", "#FF6433", "#FF3333"]

        # Current resources in this location
        self.current_resources = {}


    def activate_emergency(self, emergency):
        self.emergency = emergency
        self.color = self.color_scale[emergency.type-1]

    def is_emergency_active(self):
        if self.emergency != None:
            return True
        return False

    def delete_emergency(self):
        self.emergency = None
        self.color = "grey"

    def remove_resource(self, resource_id):
        del self.current_resources[resource_id]

    def add_resource(self, resource_id, resource):
        self.current_resources[resource_id] = resource

    def operating_resources(self, count):
        if len(self.current_resources) == 0:
            return None
        for resource in self.current_resources:
            if self.current_resources[resource].currently_assisting():
                count -=1
                self.current_resources[resource].dispatch_time += 1
                if count <= 0:
                    break
        return count

class Graph:

    def __init__(self, visualization):

        # The graph stucture 
        self.graph = None

        # City agent
        self.city_agent = None

        # Color map for the graph nodes
        self.color_map = []

        # Attributes reffering to emergencies
        self.total_emergencies = 0
        self.emergency_count = 0
        self.active_emergencies_list = {}

        # Predefined emergency list 
        self.emergency_cycle_list = []

        # Cycle count
        self.total_cycles = 0
        self.current_cycle_count = 0

        # Width and Height for visualization
        self.draw_width = 10
        self.draw_height = 10
        self.node_positions = {}
        self.draw_interval = 0.05

        self.figure = None
        self.axis = None
        self.axis_index_1 = None
        self.axis_index_2 = None
        self.exec_type = None
        self.behaviour = None
        self.distribution = None
        self.node_count = None

        # Fixed simulation values
        self.simulation_width = 15
        self.simulation_height = 15
        self.simulation_emergencies = 1500
        self.simulation_resources = 100
        self.simulation_cycles = 1000

        # Visualize the system
        self.visualization = True

        if visualization == 'Off':
            self.visualization = False

    def initial_setup(self, emergencies, cycles):
        self.total_emergencies = emergencies
        self.total_cycles = cycles
        self.uniform_emergency_distribution()
        self.draw_interval = 10/self.total_cycles

    def initial_setup_simulation(self, simul_type):
        self.generate_grid_graph(self.simulation_width, self.simulation_height)
        self.total_emergencies = self.simulation_emergencies
        self.total_cycles = self.simulation_cycles

        if simul_type == "Uniform":
            self.uniform_emergency_distribution()
        elif simul_type == "Normal":
            self.normal_emergency_distribution()
        elif simul_type == "Linear":
            self.linear_emergency_distribution()
        elif simul_type == "Exponential":
            self.exponential_emergency_distribution()

        return [self.simulation_resources, self.simulation_emergencies, self.simulation_cycles, self.simulation_width*self.simulation_height]

    def cycle_passed(self, cycle_count):

        available_agents = dict(self.city_agent.available_agents)
        unsatisfied_emergencies = self.city_agent.unsatisfied_emergencies

        for agent_id in available_agents:
            if len(unsatisfied_emergencies) > 0:
                self.city_agent.dispatch_closest_emergency(available_agents[agent_id])
                
        emergency_list = list(self.active_emergencies_list)
        for emergency in emergency_list:
            result = self.active_emergencies_list[emergency].update_counter()

            if not result:
                self.delete_emergency(self.active_emergencies_list[emergency])

        self.generate_emergencies()
        self.current_cycle_count+= 1

        if self.visualization:
            self.draw_graph()

    def remove_resource(self, current_location, resource_id):
        self.graph.nodes[current_location]["node"].remove_resource(resource_id)


    def add_resource(self, next_location, resource_id, resource):
        self.graph.nodes[next_location]["node"].add_resource(resource_id, resource)

    def delete_emergency(self, emergency):
        self.city_agent.delete_emergency(emergency)
        self.active_emergencies_list[emergency.id].delete_self()
        del self.active_emergencies_list[emergency.id]
        

    def generate_emergencies(self):
        while self.emergency_cycle_list and self.emergency_cycle_list[0][0] == self.current_cycle_count:
            new_emergency = Emergency()
            emergency_id = self.emergency_count
            location = self.random_graph_free_emergency_position()
            emergency_type = self.emergency_cycle_list[0][1]

            if location != None:
                node = self.graph.nodes[location]["node"]
                new_emergency.initial_setup(emergency_id, location, emergency_type, node)

                self.emergency_count += 1 
                self.active_emergencies_list[emergency_id] = new_emergency

                node.activate_emergency(new_emergency)
                self.city_agent.register_emergency(new_emergency)

            self.emergency_cycle_list = self.emergency_cycle_list[1:]

    def generate_grid_graph(self, width, height):
        self.graph = nx.grid_2d_graph(width,height)

        row_padding = self.draw_width / width
        column_padding = self.draw_height / height

        for node in self.graph:
            self.graph.nodes[node]["node"] = GraphNode()
            self.node_positions[node] = np.array([node[0]*row_padding, node[1]*column_padding])
            
    def end_visualize_graph(self):
        plt.close()

    def visualize_graph(self):
        if self.visualization:
            self.figure = plt.figure(figsize=(2*self.draw_width,self.draw_height))
            plt.ion()
            plt.show()
            figure, self.axis = plt.subplots(1, 2, num = 1)
            self.node_count = self.simulation_width*self.simulation_height

            figure.suptitle(str(self.exec_type)+" with "+str(self.node_count)+" Nodes - current cycle "+str(self.current_cycle_count+1), fontsize=25)
            figure.text(0.18, 0.10, "Emergency distribution: "+self.distribution, fontsize=20)
            figure.text(0.66, 0.10, "Agent behaviour: "+self.behaviour, fontsize=20)
            figure.text(0.24, 0.04, "Total Resources: "+str(self.simulation_resources)+",    Total Emergencies: "+str(self.total_emergencies)+",    Total Cycles: "+str(self.total_cycles), fontsize=20)
            self.axis_index_1 = np.unravel_index(0,self.axis.shape)
            self.axis_index_2 = np.unravel_index(1,self.axis.shape)

            self.axis[self.axis_index_1].set_title("Active emergencies", fontsize=25)
            self.axis[self.axis_index_1].set_xlabel("Emergency distribution: "+self.distribution,fontsize=20)
            self.axis[self.axis_index_1].set_axis_off()

            self.axis[self.axis_index_2].set_title("Resource distribution per location", fontsize=25)
            self.axis[self.axis_index_2].set_xlabel("Agent behaviour: "+self.behaviour,fontsize=20)
            self.axis[self.axis_index_2].set_axis_off()

    def draw_graph(self):
        self.color_map = []
        resources_locations = self.city_agent.get_resources_locations()
        draw_locations = {}
        node_colors = []
        self.axis[self.axis_index_1].clear()
        self.axis[self.axis_index_2].clear()

        self.figure.suptitle(str(self.exec_type)+" with "+str(self.node_count)+" Nodes - current cycle "+str(self.current_cycle_count), fontsize=25)

        self.axis[self.axis_index_1].set_title("Active emergencies", fontsize=20)
        self.axis[self.axis_index_1].set_axis_off()
        

        self.axis[self.axis_index_2].set_title("Resource distribution per location",fontsize=20)
        self.axis[self.axis_index_2].set_axis_off()

        for node in self.graph:
            self.color_map.append(self.graph.nodes[node]["node"].color)
            if node not in resources_locations:
                    draw_locations[node] = ""
                    node_colors.append("grey")
            else:
                draw_locations[node] = resources_locations[node]
                node_colors.append("#89cff0")
        
        plt.sca(self.axis[self.axis_index_1])
        nx.draw_networkx(self.graph, pos=self.node_positions, with_labels=False, node_color=self.color_map, ax=self.axis[self.axis_index_1])


        plt.sca(self.axis[self.axis_index_2])
        nx.draw_networkx(self.graph, pos=self.node_positions, with_labels=True, node_color = node_colors, node_shape = "s",labels=draw_locations, font_size = 20, font_weight = "bold", ax=self.axis[self.axis_index_2])

        plt.draw()
        plt.pause(self.draw_interval)

    def random_graph_position(self):
        shuffled_nodes = list(self.graph.nodes)
        np.random.shuffle(shuffled_nodes)
        return shuffled_nodes[0]

    def random_graph_free_emergency_position(self):
        shuffled_nodes = list(self.graph.nodes)
        np.random.shuffle(shuffled_nodes)
        for node in shuffled_nodes:
            if not self.graph.nodes[node]["node"].is_emergency_active():
                return node
        return None

    def random_emergency_grade_normal(self):
        return np.random.choice([1,2,3,4,5], p=[0.30, 0.25, 0.20, 0.15, 0.10])

    def uniform_emergency_distribution(self):
        distribution = np.sort(np.random.random_integers(0, self.total_cycles-1, self.total_emergencies))

        for cycle in distribution:
            self.emergency_cycle_list.append((cycle,self.random_emergency_grade_normal()))

    def normal_emergency_distribution(self):
        distribution = np.sort(get_truncated_normal(self.total_cycles/2,self.total_cycles/3, 0, self.total_cycles-1).rvs(self.total_emergencies))

        for cycle in distribution:
            self.emergency_cycle_list.append((int(round(cycle)),self.random_emergency_grade_normal()))

    def linear_emergency_distribution(self):
        distribution = list(np.sort(np.random.triangular(0, self.total_cycles-1,self.total_cycles-1, self.total_emergencies)))

        for cycle in distribution:
            self.emergency_cycle_list.append((int(round(cycle)),self.random_emergency_grade_normal()))

    def exponential_emergency_distribution(self):
        distribution = np.sort(get_truncated_exponential(0, self.total_cycles-1, self.total_cycles/32).rvs(self.total_emergencies))

        distribution2 = []
        for element in distribution:
            distribution2.append(self.total_cycles-1-element)
        distribution2 = np.sort(distribution2)

        for cycle in distribution2:
            self.emergency_cycle_list.append((int(round(cycle)),self.random_emergency_grade_normal()))

    def debug_log(self):
        return self.graph.nodes

class Emergency:

    def __init__(self):
        # Emergency identifier
        self.id = None

        #Location in the graph node
        self.location = None

        # Graph node emergency belongs to
        self.node = None

        #Type of emergency
        self.type = None

        #State of emergency
        self.active = True

        #Time since emergency started
        self.longevity = 0 

        #Time until first responder is on scene
        self.response_time = None 

        #Internal Counter
        self.count = 0

    def initial_setup(self, id, location, emergency_type, node):
        self.id = id
        self.location = location
        self.type = emergency_type
        self.node = node

        if self.type != None:
            if self.type == 1:
                self.count = np.random.random_integers(4,8)
            elif self.type == 2:
                self.count = np.random.random_integers(10,15)
            elif self.type == 3:
                self.count = np.random.random_integers(25,35)
            elif self.type == 4:
                self.count = np.random.random_integers(55,70)
            else:
                self.count = np.random.random_integers(100,150)

    def update_counter(self):
        if self.active:
            self.longevity += 1

        count = self.node.operating_resources(self.count)

        if count != None:
            if self.response_time == None:
                self.response_time = self.longevity
            self.count = count

        if self.count <= 0:
            return False

        return True

    def delete_self(self):
        self.node.delete_emergency()
