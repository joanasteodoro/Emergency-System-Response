import networkx as nx 
import matplotlib.pyplot as plt
import click as click
import math
import graphs as graphs
import numpy as np

class City_Agent:

    def __init__(self):

        #City graph
        self.city_graph = None

        #Dictionary of all agents
        self.resource_agents_list = {}

        #Dictionaries 
        self.available_agents = {}
        self.unavailable_agents = {}

        self.active_emergencies = {}

        self.unsatisfied_emergencies = {}

        self.emergency_evaluation = {}
        self.emergency_evaluation_history = {}

        self.emergency_time = {}

        self.stations = {}

    def initial_setup(self, graph, resources, behaviour):
        self.register_graph(graph)

        #TODO make different possibilities
        for i in range(1, 6):
            self.emergency_evaluation[i] = 0
            self.emergency_evaluation_history[i] = []
            self.emergency_time[i] = []

        if behaviour == "Station" or behaviour == "Mix":
            for i in range(int(math.sqrt(graph.graph.size()))):
                self.stations[i] = graph.random_graph_position()

        self.resource_agents_list = {}
        self.available_agents = {}
        self.unavailable_agents = {}

        for i in range(resources):
            resource_agent = Resource_Agent()
            if behaviour == "Mix":
                current_behaviour = np.random.choice(["Idle","Patrol","Station"])
            else:
                current_behaviour = behaviour
            if current_behaviour == "Station":
                location = self.stations[np.random.randint(len(self.stations))]
            else:
                location = graph.random_graph_position()
            resource_agent.initial_setup(i, graph, location, current_behaviour, self)
            self.register_agent(resource_agent)


    def register_graph(self, graph):
        self.city_graph = graph

    def register_agent(self, agent):
        if agent.name not in self.resource_agents_list:
            self.resource_agents_list[agent.name] = agent
            self.available_agents[agent.name] = agent
            self.city_graph.add_resource(agent.current_location, agent.name, agent)

    def register_available_agent(self, agent):
        if agent.name not in self.available_agents:
            self.available_agents[agent.name] = agent
            if agent.name in self.unavailable_agents:
                del self.unavailable_agents[agent.name]

    def dispatch_closest_emergency(self, agent):
        if len(self.unsatisfied_emergencies) == 0:
            return
        path_lengths = {}
        for emergency_id in self.unsatisfied_emergencies:
            emergency = self.unsatisfied_emergencies[emergency_id][0]
            path_lengths[emergency_id] = len(agent.evaluate_shortest_path(agent.current_location, emergency.location))
        emergency_id = min(path_lengths, key=path_lengths.get)
        emergency = self.unsatisfied_emergencies[emergency_id][0]
        resources_left = self.unsatisfied_emergencies[emergency_id][1]
        if(resources_left <= 0):
            del self.unsatisfied_emergencies[emergency_id]
        else:
            self.unsatisfied_emergencies[emergency_id] = (emergency, resources_left-1)
        agent.receive_emergency(emergency)
        self.register_unavailable_agent(agent)
        

    def closest_station(self, agent):
        if len(self.stations) == 0:
            return None
        path = {}
        path_lengths = {}
        for station_id in self.stations:
            station = self.stations[station_id]
            path[station_id] = agent.evaluate_shortest_path(agent.current_location, station)
            path_lengths[station_id] = len(path[station_id])
        station_id = min(path_lengths, key=path_lengths.get)
        
        if len(path[station_id]) > 1:
            return path[station_id][1]
        else:
            return path[station_id][0]

    def register_unavailable_agent(self, agent):
        if agent.name not in self.unavailable_agents:
            self.unavailable_agents[agent.name] = agent

        if agent.name in self.available_agents:
            del self.available_agents[agent.name]

    def register_emergency(self, emergency):
        if emergency.id not in self.active_emergencies:
            self.active_emergencies[emergency.id] = emergency
            resources_needed = self.emergency_evaluation[emergency.type]
            if resources_needed <= 0:
                resources_needed = 1
            self.dispatch_resources(emergency, resources_needed)

    def update_emergency_evaluation(self, emergency, severity):
        self.emergency_evaluation_history[emergency.type].append(severity)
        self.emergency_evaluation[emergency.type] = int(np.mean(self.emergency_evaluation_history[emergency.type]))

    def delete_emergency(self, emergency):
        unavailable_agents_list = list(self.unavailable_agents)

        total_severity = 0
        total_agents = 0

        for agent_id in unavailable_agents_list:
            agent = self.unavailable_agents[agent_id]

            if agent.emergency_location == emergency.location:
                total_severity = agent.calculate_severity()
                total_agents += 1
                agent.end_emergency()
        
        self.update_emergency_evaluation(emergency, total_severity / total_agents)

        self.emergency_time[emergency.type].append((emergency.response_time, emergency.longevity - emergency.response_time))

        if emergency.id in self.unsatisfied_emergencies:
            del self.unsatisfied_emergencies[emergency.id]
        del self.active_emergencies[emergency.id]

    def dispatch_resources(self, emergency, resources_needed):
        path_lengths = {}

        for agent_id in self.available_agents:
            agent = self.available_agents[agent_id]
            path_lengths[agent_id] = len(agent.evaluate_shortest_path(agent.current_location, emergency.location))

        for i in range(resources_needed):
            if path_lengths == {}:
                self.unsatisfied_emergencies[emergency.id] = (emergency, resources_needed - i)
                return
            agent_id = min(path_lengths, key=path_lengths.get)
            agent = self.available_agents[agent_id]

            agent.receive_emergency(emergency)
            self.register_unavailable_agent(agent)
            del path_lengths[agent_id]

    def get_resources_locations(self):
        resource_list = {}

        for agent in self.resource_agents_list:
            location = self.resource_agents_list[agent].current_location
            if location in resource_list:
                resource_list[location] += 1
            else:
                resource_list[location] = 1

        return resource_list

    def move_resource(self, resource_id, current_location, next_location):
        self.city_graph.remove_resource(current_location, resource_id)
        self.city_graph.add_resource(next_location, resource_id, self.resource_agents_list[resource_id])

    def calculate_response_success(self):
        
        total_recorded_responses = 0
        total_succesful_responses = 0
        first_response = [12,10,8,7,5]
        resolution_time = [5,6,8,12,16]
        response_success = {}

        for i in range(5):
            num_recorded_responses = 0
            num_succesful_responses = 0
        
            for t in self.emergency_time[i + 1]:
                if t[0] <= first_response[i] and t[1] <= resolution_time[i]:
                    num_succesful_responses += 1
                num_recorded_responses += 1

            if num_recorded_responses != 0:
                response_success[i + 1] =  (num_succesful_responses / num_recorded_responses) * 100
            
            total_recorded_responses += num_recorded_responses
            total_succesful_responses += num_succesful_responses

        if total_recorded_responses != 0:
            response_success[0] = (total_succesful_responses / total_recorded_responses) * 100
        return response_success


    def debug_log(self):
        print("\nCity Graph: ")
        print(self.city_graph.debug_log())

        print("\nResource Agents List: ")
        print(self.resource_agents_list)

        print("\nAvailable Agent List: ")
        print(self.available_agents)

        print("\nUnavailable Agent List: ")
        print(self.unavailable_agents)

        print("\nActive Emergencies: ")
        print(self.active_emergencies)


class Resource_Agent:

    def __init__(self):

        #Agent name
        self.name = None
        
        #City graph
        self.city_graph = None

        #Main agent responsible for all coordination
        self.city_agent = None

        #Current location in the graph node
        self.current_location = None

        #Availability status
        self.available = True

        #Current Emergency State
        self.active_emergency = None

        #Emergency Location
        self.emergency_location = None

        #Time Handling emergency
        self.dispatch_time = None

        #Time going to emergency
        self.travel_time = None

        #Movement Behaviour
        self.behaviour = None

        #Assigned Station
        self.station = None

    def initial_setup(self, name, graph, current_location, behaviour, city_agent):
        self.name = name
        self.city_graph = graph
        self.current_location = current_location
        self.city_agent = city_agent
        self.behaviour = behaviour
        if behaviour == "Station":
            self.station = city_agent.closest_station(self)

    def receive_emergency(self, received_emergency):
        if self.available:
            self.active_emergency = received_emergency
            self.emergency_location = received_emergency.location
            self.available = False
            self.dispatch_time = 0
            self.travel_time = 0

    def end_emergency(self):
        if self.active_emergency != None:
            self.available = True
            self.active_emergency = None
            self.emergency_location = None
            self.dispatch_time = 0
            self.travel_time = 0

        self.city_agent
        self.city_agent.register_available_agent(self)

    def calculate_severity(self):
        if self.dispatch_time > 0:
            return self.dispatch_time + self.travel_time
        else:
            return -1

    def move_agent(self):
        if not self.available and self.emergency_location != None:
            if self.current_location != self.emergency_location:
                next_position = self.next_position(self.emergency_location)
                self.city_agent.move_resource(self.name, self.current_location, next_position)
                self.current_location = next_position
                self.travel_time += 1
        else:
            if self.behaviour == "Idle":
                return
            elif self.behaviour == "Patrol":
                adj_positions = list(self.city_agent.city_graph.graph.neighbors(self.current_location))
                next_position = adj_positions[np.random.randint(len(adj_positions))]
                self.city_agent.move_resource(self.name, self.current_location, next_position)
                self.current_location = next_position
            elif self.behaviour == "Station":
                if self.current_location not in self.city_agent.stations:
                    next_position = self.next_position(self.station)
                    self.city_agent.move_resource(self.name, self.current_location, next_position)
                    self.current_location = next_position

    def next_position(self, location):
        path = self.evaluate_shortest_path(self.current_location, location)
        if len(path) > 1:
            return path[1]
        else:
            return path[0]

    def evaluate_shortest_path(self, source, destiny, weight=None):
        return nx.shortest_path(self.city_graph.graph, source = source, target = destiny)

    def currently_assisting(self):
        return self.emergency_location != None and self.current_location == self.emergency_location 

    def debug_log(self):
        print("Resource Agent name: " + str(self.name))
        print("Current location: " + str(self.current_location))
        print("Availability: " + str(self.available))
        print("Active Emergency: " + str(self.active_emergency))
        print("Emergency location: " + str(self.emergency_location))        