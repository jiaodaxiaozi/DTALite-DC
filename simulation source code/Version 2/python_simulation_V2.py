# -*- coding: utf-8 -*-
"""
Created on Sun Oct  7 21:05:13 2018

@author: jiaweil9
"""

import pandas as pd
import numpy as np
from collections import deque
import csv

g_number_of_seconds_per_interval = 0.2
g_start_simu_interval_no = 0
g_number_of_demand_types = 2
g_Simulation_StartTimeInMin = 9999
g_Simulation_EndTimeInMin = 0
g_number_of_simulation_time_intervals = int(20*60 / g_number_of_seconds_per_interval)
MAX_LABEL_COST = float('inf')
g_total_assignment_iteration = 1
g_safe_headway = 1.4
probability_of_lane_changing = 0.06
working_directory = r'test_network\\'     #absolute path or relative path, blank string if data saved in cwd

g_micro_node_list = []
g_micro_link_list = []
g_agent_list = []
g_macro_node_list = []
g_macro_link_list = []
g_internal_macro_node_seq_no_dict = {}
g_internal_macro_link_seq_no_dict = {}
g_macro_node_id_dict = {}
g_internal_micro_node_seq_no_dict = {}
g_micro_node_id_dict = {}
g_link_key_to_seq_no_dict = {}
g_internal_agent_seq_no_dict = {}
g_micro_destination_seq_no_list = []
g_active_agent_queue = deque()

g_number_of_macro_nodes = 0
g_number_of_macro_links = 0
g_number_of_micro_nodes = 0
g_number_of_micro_links = 0
g_number_of_agents = 0
g_start_simu_interval_no = 0
g_end_simu_interval_no = 0


class MacroNode:
    def __init__(self,name,node_id,zone_id,micro_node_set,control_type,control_type_name,cycle_length_in_second,x,y,geometry):
        self.name = name
        self.node_id = int(node_id)
        self.zone_id = int(zone_id)
        if self.zone_id != -1:
            self.micro_node_set_out = [int(node) for node in micro_node_set.split(';')[0].split(',')]
            self.micro_node_set_in = [int(node) for node in micro_node_set.split(';')[1].split(',')]
        else:
            self.micro_node_set_out = []
            self.micro_node_set_out = []
            
        self.control_type = int(control_type) if control_type else -1
        self.control_type_name = control_type_name
        self.cycle_length_in_second = int(cycle_length_in_second) if cycle_length_in_second else -1
        self.x = float(x) if x else -1
        self.y = float(y) if y else -1
        self.geometry_str = geometry
        self.m_outgoing_link_list = []
        self.m_incoming_link_list = []
        self.Initialization()
        
    def Initialization(self):
        global g_number_of_macro_nodes
        g_internal_macro_node_seq_no_dict[self.node_id] = g_number_of_macro_nodes
        g_macro_node_id_dict[g_number_of_macro_nodes] = self.node_id
        self.node_seq_no = g_number_of_macro_nodes
        
        g_number_of_macro_nodes += 1
        if g_number_of_macro_nodes % 1000 == 0:
            print('reading',g_number_of_macro_nodes, 'nodes')
        

class MacroLink:
    def __init__(self,name,link_id,link_key,speed_sensor_id,count_sensor_id,from_node_id,to_node_id,link_type_name,direction,length,number_of_lanes,
                 speed_limit,lane_cap,link_type,jam_density,wave_speed,demand_type_code,mode_code,network_design_flag,grade,geometry,original_geometry,
                 map_matching_orientation_code,map_matching_loop_code,additional_lanes_on_left_side,length_of_left_side_lanes,additional_lanes_on_right_side,
                 length_of_right_side_lanes):
        self.link_id = int(link_id)
        self.from_node_id = int(from_node_id)
        self.to_node_id = int(to_node_id)
        self.length = float(length)
        self.number_of_lanes = int(number_of_lanes)
        self.speed_limit = float(speed_limit)
        self.lane_cap = int(lane_cap)
        self.flow_volume = 0
        self.BRP_alpha = 0.15
        self.BRP_beta = 4.0
        self.link_capacity = self.number_of_lanes*self.lane_cap
        self.free_flow_travel_time_in_min = self.length / self.speed_limit * 60
        self.free_flow_travel_time_in_simu_interval = round(self.free_flow_travel_time_in_min*60 / g_number_of_seconds_per_interval)
        self.m_active_agent_queue = deque()
        
        self.micro_node_list = []
        self.potential_micro_incoming_node_seq_no_list = []
        self.potential_micro_outgoing_node_seq_no_list = []
        self.micro_incoming_node_seq_no_list = []
        self.micro_outgoing_node_seq_no_list = []
        self.turning_node_seq_no_dict = {}             #macro_link_seq_no:micro_node_seq_no
        self.estimated_cost_tree_for_each_movement = {}     #macro_link_seq_no:cost_array
        
        self.CalculateBPRFunctionAndCost()
        self.Initialization()
    
    def Initialization(self):
        global g_number_of_macro_links
        
        self.from_node_seq_no = g_internal_macro_node_seq_no_dict[self.from_node_id]
        self.to_node_seq_no = g_internal_macro_node_seq_no_dict[self.to_node_id]
        self.link_seq_no = g_number_of_macro_links
        g_internal_macro_link_seq_no_dict[self.link_id] = self.link_seq_no
#        demand_type_code
        g_macro_node_list[self.from_node_seq_no].m_outgoing_link_list.append(self)
        g_macro_node_list[self.to_node_seq_no].m_incoming_link_list.append(self)
        link_key = self.from_node_seq_no * 1000000 + self.from_node_seq_no
        
        g_link_key_to_seq_no_dict[link_key] = self.link_seq_no
        
        g_number_of_macro_links += 1
        if g_number_of_macro_links % 1000 == 0:
            print('reading',g_number_of_macro_links, 'links')
    
    def CalculateBPRFunctionAndCost(self):
        self.travel_time = self.free_flow_travel_time_in_min*(1 + self.BRP_alpha*pow(self.flow_volume / max(0.00001, self.link_capacity), self.BRP_beta))
        self.cost = self.travel_time
        


class MicroNode:
    def __init__(self,node_id,x,y,macro_link_id,lane_no):

        self.node_id = int(node_id)
        self.node_seq_no = 0
        self.x = float(x)
        self.y = float(y)
        self.macro_link_id = int(macro_link_id) if macro_link_id else -1
        self.lane_no = int(lane_no) if lane_no else -1
        self.m_outgoing_link_list = []
        self.m_incoming_link_list = []
        self.available_sim_interval = 0
        
        self.Initialization()
        
    def Initialization(self):
        global g_number_of_micro_nodes
        g_internal_micro_node_seq_no_dict[self.node_id] = g_number_of_micro_nodes
        g_micro_node_id_dict[g_number_of_micro_nodes] = self.node_id
        self.node_seq_no = g_number_of_micro_nodes
        
        g_number_of_micro_nodes += 1
        if g_number_of_micro_nodes % 1000 == 0:
            print('reading',g_number_of_micro_nodes, 'nodes')
    
    def AllocateMemory(self):
        self.tree_cost = np.zeros(g_number_of_micro_nodes)
        

class MicroLink:
    def __init__(self,link_id,from_node_id,to_node_id,macro_link_id,lane_no,link_type,length,speed_limit,additional_cost):
        self.link_id = int(link_id)
        self.from_node_id = int(from_node_id)
        self.to_node_id = int(to_node_id)     
        self.macro_link_id = int(macro_link_id)
        self.lane_no = int(lane_no) if lane_no else -1
        self.macro_link_seq_no = g_internal_macro_link_seq_no_dict[self.macro_link_id]
        self.length = float(length)
        self.speed_limit = float(speed_limit)
        self.link_type = link_type
        self.flow_volume = 0
        self.free_flow_travel_time_in_min = self.length / self.speed_limit * 60
        self.free_flow_travel_time_in_simu_interval = round(self.free_flow_travel_time_in_min*60 / g_number_of_seconds_per_interval * float(additional_cost))
        self.cost = self.free_flow_travel_time_in_simu_interval
        self.m_active_agent_queue = deque()

        self.Initialization()
    
    
    def Initialization(self):
        global g_number_of_micro_links
        
        self.from_node_seq_no = g_internal_micro_node_seq_no_dict[self.from_node_id]
        self.to_node_seq_no = g_internal_micro_node_seq_no_dict[self.to_node_id]
        self.link_seq_no = g_number_of_micro_links

        g_micro_node_list[self.from_node_seq_no].m_outgoing_link_list.append(self)
        g_micro_node_list[self.to_node_seq_no].m_incoming_link_list.append(self)
        link_key = self.from_node_seq_no * 1000000 + self.from_node_seq_no
        g_link_key_to_seq_no_dict[link_key] = self.link_seq_no
        
        g_macro_link_list[self.macro_link_seq_no].potential_micro_incoming_node_seq_no_list.append(self.from_node_seq_no)
        g_macro_link_list[self.macro_link_seq_no].potential_micro_outgoing_node_seq_no_list.append(self.to_node_seq_no)
        
        g_number_of_micro_links += 1
        if g_number_of_micro_links % 1000 == 0:
            print('reading',g_number_of_micro_links, 'links')
        
       

class Agent:
    def __init__(self, agent_type, from_zone_id, tour_id, to_zone_id, from_origin_node_id, 
                 to_destination_node_id, departure_time_in_min):
        
        self.agent_type = agent_type
        self.origin_zone_id = int(from_zone_id)
        self.tour_id = tour_id
        self.destination_zone_id = int(to_zone_id)

        self.macro_origin_node_id = int(from_origin_node_id)
        self.macro_destination_node_id = int(to_destination_node_id)
        self.macro_origin_node_seq_no = g_internal_macro_node_seq_no_dict[self.macro_origin_node_id]
        self.macro_destination_node_seq_no = g_internal_macro_node_seq_no_dict[self.macro_destination_node_id]
        self.micro_origin_node_id = np.random.choice(g_macro_node_list[self.macro_origin_node_seq_no].micro_node_set_out)
        self.micro_destination_node_id = 0
        self.micro_origin_node_seq_no = g_internal_micro_node_seq_no_dict[self.micro_origin_node_id]
        self.micro_destination_node_seq_no = 0
        if self.micro_destination_node_seq_no not in g_micro_destination_seq_no_list:
            g_micro_destination_seq_no_list.append(self.micro_destination_node_seq_no)
        self.departure_time_in_min = np.random.uniform(int(departure_time_in_min),int(departure_time_in_min)+0.999)
        self.arrival_time_in_min = 0.0
        self.arrival_time_in_simu_interval = 0
        self.travel_time_in_min = 0.0

        self.macro_path_node_seq_no_list = []
        self.macro_path_link_seq_no_list = []
        self.path_node_seq_str = ''
        self.path_time_seq_str = ''
        self.path_node_id_list = []
        self.number_of_nodes = 0
        self.fixed_path_flag = 0
        self.demand_type = 1 
        self.m_bMoveable = 1
        self.origin_zone_seq_no = 0
        self.destination_zone_seq_no = 0

        self.dependency_agent_id = 0
        self.duration_in_min = 0
        self.following_agent_id = 0
        self.departure_time_in_simu_interval = round(self.departure_time_in_min / g_number_of_seconds_per_interval * 60)
        self.PCE_factor = 1.0
        self.path_cost = 0
        self.m_path_link_seq_no_list_size = 0
        self.path_schedule_time_list = []
        self.m_current_link_seq_no = 0
        self.latest_arrival_time = 0.0
        
        self.micro_path_node_seq_no_list = []
        self.micro_path_link_seq_no_list = []
        self.micro_path_node_id_list = []
        self.micro_path_link_id_list = []
        
        self.m_Veh_LinkArrivalTime_in_simu_interval = []
        self.m_Veh_LinkDepartureTime_in_simu_interval = []
        
        self.path_timestamp_list = []
        
        self.current_macro_path_seq_no = 0
        self.current_macro_link_seq_no = 0
        self.next_macro_link_seq_no = 0
        self.m_bCompleteTrip = False
    
        self.Initialization()
    
    def Initialization(self):
        global g_number_of_agents
        global g_Simulation_StartTimeInMin
        global g_Simulation_EndTimeInMin
        global g_number_of_simulation_time_intervals
        if (self.macro_origin_node_id not in g_macro_node_id_dict.values()) or (self.macro_destination_node_id not in g_macro_node_id_dict.values()):
            print('agent',self.agent_id, 'origin or destination node does not exist in node set, please check!')
        else:
            self.agent_list_seq_no = g_number_of_agents
            self.agent_id = g_number_of_agents
            g_internal_agent_seq_no_dict[self.agent_id] = g_number_of_agents
            
            if self.departure_time_in_min < g_Simulation_StartTimeInMin:
                g_Simulation_StartTimeInMin = self.departure_time_in_min
            if self.departure_time_in_min > g_Simulation_EndTimeInMin:
                g_Simulation_EndTimeInMin = self.departure_time_in_min
            if self.latest_arrival_time >= g_number_of_simulation_time_intervals:
                g_number_of_simulation_time_intervals = self.latest_arrival_time + 1

            g_number_of_agents += 1
            if g_number_of_agents % 1000 == 0:
                print('reading',g_number_of_agents, 'agents')
        

            
    def FieldCalculation(self):
        self.arrival_time_in_min = self.arrival_time_in_simu_interval * g_number_of_seconds_per_interval / 60
        self.travel_time_in_min = self.arrival_time_in_min - self.departure_time_in_min
        self.path_node_seq_str = GenerateStrFromList(self.micro_path_node_id_list)
        self.path_time_seq_str = GenerateStrFromList([el*0.2/60 for el in self.m_Veh_LinkDepartureTime_in_simu_interval])
        self.number_of_nodes = len(self.micro_path_node_seq_no_list)


class Network:
    def __init__(self,m_node_list,m_link_list,network_type):        #1-marco,2-micro
        if network_type == 2:
            for node in m_node_list: node.m_incoming_link_list,node.m_outgoing_link_list = node.m_outgoing_link_list,node.m_incoming_link_list
            for link in m_link_list: link.from_node_seq_no,link.to_node_seq_no = link.to_node_seq_no,link.from_node_seq_no
        self.m_node_list = m_node_list
        self.m_link_list = m_link_list           
    
    
    def AllocateMemory(self):
        m_number_of_nodes = len(self.m_node_list)
        self.node_status_array = np.ones(m_number_of_nodes, dtype = int)
        self.node_predecessor = np.ones(m_number_of_nodes, dtype = int) * -1
        self.node_label_cost = np.ones(m_number_of_nodes) * MAX_LABEL_COST
        self.link_predecessor = np.ones(m_number_of_nodes, dtype = int) * -1
#        self.link_cost_array = np.zeros(g_number_of_links)
        self.node2node_accessibility_list = []
#        self.link_volume_array = np.zeros(g_number_of_links)
    
    def optimal_label_correcting(self,origin_node,destination_node,departure_time_in_min):
        if len(self.m_node_list[origin_node].m_outgoing_link_list) == 0:
            return 0
                
        self.AllocateMemory()
        self.node_label_cost[origin_node] = departure_time_in_min
        SEList = deque()
        SEList.append(origin_node)

        while len(SEList)>0:
            from_node = SEList[0]
            SEList.popleft()
            for outgoing_link in self.m_node_list[from_node].m_outgoing_link_list:
                to_node = outgoing_link.to_node_seq_no
                b_node_updated = False
                new_to_node_cost = self.node_label_cost[from_node] + outgoing_link.cost
                if (new_to_node_cost < self.node_label_cost[to_node]):  #we only compare cost at the downstream node ToID at the new arrival time t
                    self.node_label_cost[to_node] = new_to_node_cost
                    self.node_predecessor[to_node] = from_node  #pointer to previous physical NODE INDEX from the current label at current node and time
                    self.link_predecessor[to_node] = outgoing_link.link_seq_no  #pointer to previous physical NODE INDEX from the current label at current node and time
                    b_node_updated = True                                        
                    SEList.append(to_node)
                    self.node_status_array[to_node] = 1

        if (destination_node >= 0 and self.node_label_cost[destination_node] < MAX_LABEL_COST):
            return 1
        elif (destination_node == -1):
            return 1 # one to all shortest path
        else: 
            return -1


    def find_path_for_agents(self,iteration_no):
        #step 1: find shortest path if needed 
        for i in range(len(g_agent_list)):
            residual = i % (iteration_no + 1)
            if (residual != 0):
                continue 
 
            g_agent_list[i].macro_path_link_seq_no_list = []
            g_agent_list[i].macro_path_node_seq_no_list = []
            return_value = self.optimal_label_correcting(g_agent_list[i].macro_origin_node_seq_no, g_agent_list[i].macro_destination_node_seq_no, g_agent_list[i].departure_time_in_min)

            if (return_value == -1):
                print('agent ',i,'can not find destination node')
                continue

            current_node_seq_no = g_agent_list[i].macro_destination_node_seq_no
            g_agent_list[i].path_cost = self.node_label_cost[g_agent_list[i].macro_destination_node_seq_no]
                        
            while (current_node_seq_no>=0):
                if (current_node_seq_no >= 0):  #this is valid node 
                    current_link_seq_no = self.link_predecessor[current_node_seq_no]
                            
                    if(current_link_seq_no>=0):
                        g_agent_list[i].macro_path_link_seq_no_list.append(current_link_seq_no)      

                    g_agent_list[i].macro_path_node_seq_no_list.append(current_node_seq_no)

                current_node_seq_no = self.node_predecessor[current_node_seq_no]
            
            g_agent_list[i].macro_path_node_seq_no_list.reverse()
            g_agent_list[i].macro_path_link_seq_no_list.reverse()
            
            number_of_links_in_path = len(g_agent_list[i].macro_path_link_seq_no_list)
            for j in range(number_of_links_in_path):
                g_macro_link_list[g_agent_list[i].macro_path_link_seq_no_list[j]].flow_volume += g_agent_list[i].PCE_factor



def NetworkInfoCalculation():
    for link in g_macro_link_list:
        link.micro_incoming_node_seq_no_list = list(set(link.potential_micro_incoming_node_seq_no_list) - set(link.potential_micro_outgoing_node_seq_no_list))
        link.micro_outgoing_node_seq_no_list = list(set(link.potential_micro_outgoing_node_seq_no_list) - set(link.potential_micro_incoming_node_seq_no_list))
        link.micro_node_seq_no_list = list(set(link.potential_micro_incoming_node_seq_no_list) | set(link.potential_micro_outgoing_node_seq_no_list))
    for from_link in g_macro_link_list:
        current_node = from_link.to_node_seq_no
        for micro_node_seq_no in from_link.micro_outgoing_node_seq_no_list:
            for to_link in g_macro_node_list[current_node].m_outgoing_link_list:
                if micro_node_seq_no in to_link.micro_incoming_node_seq_no_list:
                    if to_link.link_seq_no not in from_link.turning_node_seq_no_dict.keys():
                        from_link.turning_node_seq_no_dict[to_link.link_seq_no] = [micro_node_seq_no]  #macro_link_seq_no:micro_node_seq_no
                    else:
                        from_link.turning_node_seq_no_dict[to_link.link_seq_no].append(micro_node_seq_no)

    micro_network = Network(g_micro_node_list[:],g_micro_link_list[:],2)
    for link in g_macro_link_list:
        if len(link.turning_node_seq_no_dict) > 0:
            for to_link_seq_no in link.turning_node_seq_no_dict.keys():
                cost_tree = np.ones(g_number_of_micro_nodes) * float('inf')
                for outgoing_node_seq_no in link.turning_node_seq_no_dict[to_link_seq_no]:
                    return_value = micro_network.optimal_label_correcting(outgoing_node_seq_no,-1, 0)
                    if return_value == 1:
                        cost_tree = np.vstack((cost_tree,micro_network.node_label_cost)).min(axis=0)
                link.estimated_cost_tree_for_each_movement[to_link_seq_no] = cost_tree
        else:
            cost_tree = np.ones(g_number_of_micro_nodes) * float('inf')
            for outgoing_node_seq_no in link.micro_outgoing_node_seq_no_list:
                return_value = micro_network.optimal_label_correcting(outgoing_node_seq_no,-1, 0)
                if return_value == 1:
                    cost_tree = np.vstack((cost_tree,micro_network.node_label_cost)).min(axis=0)
            link.estimated_cost_tree_for_each_movement[-1] = cost_tree

    for node in micro_network.m_node_list: node.m_incoming_link_list,node.m_outgoing_link_list = node.m_outgoing_link_list,node.m_incoming_link_list
    for link in micro_network.m_link_list: link.from_node_seq_no,link.to_node_seq_no = link.to_node_seq_no,link.from_node_seq_no    
       
          
def g_ReadInputData():
    global g_macro_node_list
    global g_macro_link_list
    global g_micro_node_list
    global g_micro_link_list
    global g_agent_list
    global g_start_simu_interval_no
    global g_end_simu_interval_no

    with open(working_directory + 'input_macro_node.csv') as fin:
        reader = csv.reader(fin)
        next(reader)  # read header
        g_macro_node_list = [MacroNode(*row) for row in reader]

    with open(working_directory + 'input_macro_link.csv') as fin:
        reader = csv.reader(fin)
        next(reader)  # read header
        g_macro_link_list = [MacroLink(*row) for row in reader]

    with open(working_directory + 'input_micro_node.csv') as fin:
        reader = csv.reader(fin)
        next(reader)  # read header
        g_micro_node_list = [MicroNode(*row) for row in reader]
        
    with open(working_directory + 'input_micro_link.csv') as fin:
        reader = csv.reader(fin)
        next(reader)  # read header
        g_micro_link_list = [MicroLink(*row) for row in reader]

    with open(working_directory + 'input_demand.csv') as fin:
        reader = csv.reader(fin)
        next(reader)  # read header
        g_agent_list = [Agent(*row[1:-1]) for row in reader for i in range(int(row[-1]))]
    
    NetworkInfoCalculation()
    
    g_start_simu_interval_no = int(g_Simulation_StartTimeInMin * 60 / g_number_of_seconds_per_interval)
    g_end_simu_interval_no = int(g_start_simu_interval_no + g_number_of_simulation_time_intervals)



'''
def g_A2R_simu_interval(abs_simu_interval):
	return abs_simu_interval - g_start_simu_interval_no
'''


def g_TrafficAssignment():   
    print('Finding shortest path for all agents......')
    macro_network = Network(g_macro_node_list,g_macro_link_list,1)
    for i in range(g_total_assignment_iteration):
        print('iteration_no',i,'......')
        for l in range(g_number_of_macro_links):
            g_macro_link_list[l].CalculateBPRFunctionAndCost()
            g_macro_link_list[l].flow_volume = 0
        macro_network.find_path_for_agents(i)

       


        
def g_TrafficSimulation():   
    current_active_agent_no = 0
    number_of_simu_interval_per_min = 60 / g_number_of_seconds_per_interval
    safe_headway_in_simu_interval = round(g_safe_headway / g_number_of_seconds_per_interval)
    
    for t in range(g_start_simu_interval_no, g_end_simu_interval_no + 1):       
        if (t-g_start_simu_interval_no) % number_of_simu_interval_per_min == 0:
            while current_active_agent_no < g_number_of_agents and g_agent_list[current_active_agent_no].departure_time_in_simu_interval >= t and g_agent_list[current_active_agent_no].departure_time_in_simu_interval < t + number_of_simu_interval_per_min:
                p_agent = g_agent_list[current_active_agent_no]
                p_agent.m_bGenereated = True
                p_agent.micro_path_node_seq_no_list.append(p_agent.micro_origin_node_seq_no)
                p_agent.micro_path_node_id_list.append(p_agent.micro_origin_node_id)                 
                p_agent.m_Veh_LinkArrivalTime_in_simu_interval.append(t)
                p_agent.m_Veh_LinkDepartureTime_in_simu_interval.append(p_agent.departure_time_in_simu_interval)
                
                p_agent.current_macro_link_seq_no = p_agent.macro_path_link_seq_no_list[p_agent.current_macro_path_seq_no]
                if p_agent.current_macro_path_seq_no < len(p_agent.macro_path_link_seq_no_list)-1:
                    p_agent.next_macro_link_seq_no = p_agent.macro_path_link_seq_no_list[p_agent.current_macro_path_seq_no+1]
                else:
                    p_agent.next_macro_link_seq_no = -1
                
                g_active_agent_queue.append(current_active_agent_no)
                current_active_agent_no += 1
        
        agent_no_remove_list = []
        for agent_no in g_active_agent_queue:
            p_agent = g_agent_list[agent_no]
            if p_agent.m_Veh_LinkDepartureTime_in_simu_interval[-1] == t:
                current_node_seq = p_agent.micro_path_node_seq_no_list[-1]
                
                if t < g_micro_node_list[current_node_seq].available_sim_interval:
                    p_agent.m_Veh_LinkDepartureTime_in_simu_interval[-1] += 1
                    continue
                
                if current_node_seq in g_macro_link_list[p_agent.current_macro_link_seq_no].micro_outgoing_node_seq_no_list:
                    if p_agent.current_macro_path_seq_no == len(p_agent.macro_path_link_seq_no_list)-1:
                        agent_no_remove_list.append(agent_no)
                        p_agent.arrival_time_in_simu_interval = t
                        p_agent.micro_destination_node_id = g_micro_node_id_dict[current_node_seq]
                        p_agent.m_bCompleteTrip = True
                        continue
                    else:
                        p_agent.current_macro_path_seq_no += 1
                        p_agent.current_macro_link_seq_no = p_agent.macro_path_link_seq_no_list[p_agent.current_macro_path_seq_no]
                        if p_agent.current_macro_path_seq_no < len(p_agent.macro_path_link_seq_no_list)-1:
                            p_agent.next_macro_link_seq_no = p_agent.macro_path_link_seq_no_list[p_agent.current_macro_path_seq_no+1]
                        else:
                            p_agent.next_macro_link_seq_no = -1
                    
                min_outgoing_cost = float('inf')
                cost_list_temp = []
                for link in g_micro_node_list[current_node_seq].m_outgoing_link_list:
                    if g_internal_macro_link_seq_no_dict[link.macro_link_id] in p_agent.macro_path_link_seq_no_list:
                        cost = g_macro_link_list[p_agent.current_macro_link_seq_no].estimated_cost_tree_for_each_movement[p_agent.next_macro_link_seq_no][link.to_node_seq_no] + link.cost
                        if cost == min_outgoing_cost and cost != float('inf'):
                            cost_list_temp.append([g_macro_link_list[p_agent.current_macro_link_seq_no].estimated_cost_tree_for_each_movement[p_agent.next_macro_link_seq_no][link.to_node_seq_no],link.cost,cost,link])
                        if cost < min_outgoing_cost:
                            cost_list_temp = [[g_macro_link_list[p_agent.current_macro_link_seq_no].estimated_cost_tree_for_each_movement[p_agent.next_macro_link_seq_no][link.to_node_seq_no],link.cost,cost,link]]
                            min_outgoing_cost = cost
                if len(cost_list_temp) == 1:
                    next_link = cost_list_temp[0][3]
                else:
                    probability_list = [1-probability_of_lane_changing if el[1]==1 else probability_of_lane_changing for el in cost_list_temp]
                    cumulative_probability_list = []
                    for i in range(len(probability_list)): cumulative_probability_list.append(sum(probability_list[:i+1]))
                    rv = np.random.uniform(0,sum(probability_list))
                    for i in range(len(cumulative_probability_list)):
                        if cumulative_probability_list[i] >= rv:
                            break
                    next_link = cost_list_temp[i][3]

                g_micro_node_list[current_node_seq].available_sim_interval = t + safe_headway_in_simu_interval
                p_agent.micro_path_node_seq_no_list.append(next_link.to_node_seq_no)
                p_agent.micro_path_link_seq_no_list.append(next_link.link_seq_no)
                p_agent.micro_path_node_id_list.append(next_link.to_node_id)
                p_agent.micro_path_link_id_list.append(next_link.link_id)
                p_agent.m_Veh_LinkArrivalTime_in_simu_interval.append(t)
                p_agent.m_Veh_LinkDepartureTime_in_simu_interval.append(t+next_link.cost)
                    
        for agent_no in agent_no_remove_list: g_active_agent_queue.remove(agent_no)


def GenerateStrFromList(original_list):
    return str(original_list).replace(',', ';')[1:-1]

def OutputResults():
    with open(working_directory+'output_agent.csv', 'w', newline = '') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['agent_id','tourid','dependency_agent_id','duration_in_min','following_agent_id','from_zone_id','to_zone_id','from_origin_node_id',
                         'to_destination_node_id','departure_time_in_min','arrival_time_in_min','complete_flag','travel_time_in_min','demand_type',
                         'vehicle_type','PCE','information_type','value_of_time','toll_cost','distance','TotalEnergy_(KJ)','CO2_(g)','NOX_(g)','CO_(g)','HC_(g)',
                         'PM_(g)','PM_2.5(g)','vehicle_age','number_of_nodes','path_node_sequence','org_path_node_sequence','path_time_sequence','origin_node_x',
                         'origin_node_y','destination_node_x','destination_node_y'])
        for i in range(g_number_of_agents):
            p_agent = g_agent_list[i]
            p_agent.FieldCalculation()
            line = [p_agent.agent_id,
                    -1,-1,-1,-1,
                    p_agent.origin_zone_id,
                    p_agent.destination_zone_id,
                    p_agent.micro_origin_node_id,
                    p_agent.micro_destination_node_id,
                    p_agent.departure_time_in_min,
                    p_agent.arrival_time_in_min,
                    'c' if p_agent.m_bCompleteTrip == True else 'n',
                    p_agent.travel_time_in_min,
                    p_agent.demand_type,
                    -1,
                    p_agent.PCE_factor,
                    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
                    p_agent.number_of_nodes,
                    p_agent.path_node_seq_str,
                    -1,
                    p_agent.path_time_seq_str,
                    -1,-1,-1,-1]
            writer.writerow(line)                


if __name__ == '__main__':
    g_ReadInputData()
    g_TrafficAssignment()
    g_TrafficSimulation()
    OutputResults()
    
    
    