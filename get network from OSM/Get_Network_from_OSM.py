# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 12:44:27 2018

@author: Jiawei Lu
"""

import numpy as np
import csv

city = 'haidian district, beijing'
units = 1   #1:km,km/h;2:mile,mph
demand_generation = 1   #1:generate demand;2:not
demand_factor = 1

use_default_value = 1   #1 use default value for missing data, 2 use -1 for missing data
default_number_of_lanes = {'motorway':4,'trunk':4,'primary':3,'secondary':2,'tertiary':1,'residential':1,'others':1}
default_speed_limit = {'motorway':100,'trunk':100,'primary':80,'secondary':60,'tertiary':40,'residential':40,'others':25}

g_number_of_macro_nodes = 0
g_number_of_macro_links = 0
g_number_of_zones = 0
node_attributes_list = []
link_attributes_list = []
g_macro_node_list = []
g_macro_link_list = []
g_zone_list = []
demand_list = []
g_internal_macro_node_seq_no_dict = {}
g_internal_macro_link_seq_no_dict = {}


class MacroNode:
    def __init__(self,osmid,x,y):
        self.name = ''
        self.node_id = int(osmid)
        self.zone_id = -1
        self.micro_node_set = ''
        self.control_type = ''
        self.control_type_name = ''
        self.cycle_length_in_second = ''
        self.x = x
        self.y = y
        self.geometry = '<Point><coordinates>'+str(x)+','+str(y)+'</coordinates></Point>'
        self.m_outgoing_link_list = []      #link_seq_no
        self.m_incoming_link_list = []      #link_seq_no
        self.Initialization()
        
    def Initialization(self):
        global g_number_of_macro_nodes
        self.node_seq_no = g_number_of_macro_nodes
        g_internal_macro_node_seq_no_dict[self.node_id] = g_number_of_macro_nodes
        g_number_of_macro_nodes += 1
        

class MacroLink:
    def __init__(self,geometry,highway,lanes,length,maxspeed,name,oneway,osmid,u,v):
        self.name = name
        self.link_id = osmid[0] if isinstance(osmid,list) else osmid
        self.link_key = ''
        self.speed_sensor_id = ''
        self.count_sensor_id = ''
        self.from_node_id = u
        self.to_node_id = v
        self.link_type_name = ''
        self.direction = 1
        self.length = float(length)/1000 if units == 1 else float(length)/1000*0.6214       
        
        if (lanes != lanes or maxspeed != maxspeed) and use_default_value == 1:
            for link_type in default_number_of_lanes.keys():
                if link_type in highway: break
        
        if lanes != lanes:
            if use_default_value == 1:
                self.number_of_lanes = default_number_of_lanes[link_type]
            else:
                self.number_of_lanes = -1
        else:
            self.number_of_lanes = int(lanes) if oneway else np.ceil(int(lanes)/2)
            
        if maxspeed != maxspeed:
            if use_default_value == 1:
                self.speed_limit = default_speed_limit[link_type] if units == 1 else default_speed_limit[link_type]/1.61
                
            else:
                self.speed_limit = -1
        else:
            if (units == 1) and ('mph' not in maxspeed):
                self.speed_limit = float(maxspeed)
            elif (units == 1) and ('mph' in maxspeed):
                self.speed_limit = float(maxspeed[:-4])*1.61
            elif (units == 2) and ('mph' not in maxspeed):
                self.speed_limit = float(maxspeed)/1.61
            else:
                self.speed_limit = float(maxspeed[:-4])
            
        self.lane_cap = ''
        self.link_type = ''
        self.jam_density = ''
        self.wave_speed = ''
        self.demand_type_code = ''
        self.mode_code = ''
        self.network_design_flag = ''
        self.grade = ''
        self.geometry = '<LineString><coordinates>'+geometry.wkt[12:-1].replace(', ',',0.0;').replace(' ',',').replace(';',' ')+',0.0</coordinates></LineString>'
        self.original_geometry = ''
        self.map_matching_orientation_code = ''
        self.map_matching_loop_code = ''
        self.additional_lanes_on_left_side = ''
        self.length_of_left_side_lanes = ''
        self.additional_lanes_on_right_side = ''
        self.length_of_right_side_lanes = ''
        self.Initialization()
        
    def Initialization(self):
        global g_number_of_macro_links
        g_internal_macro_node_seq_no_dict[self.link_id] = g_number_of_macro_links
        g_number_of_macro_links += 1
        g_macro_node_list[g_internal_macro_node_seq_no_dict[self.from_node_id]].m_outgoing_link_list.append(g_number_of_macro_links)
        g_macro_node_list[g_internal_macro_node_seq_no_dict[self.to_node_id]].m_incoming_link_list.append(g_number_of_macro_links)

class Zone:
    def __init__(self,node):
        self.node_id = node.node_id
        self.node_seq_no = node.node_seq_no
        self.number_of_incoming_lanes = g_macro_link_list[node.m_incoming_link_list[0]].number_of_lanes if node.m_incoming_link_list else 0
        self.number_of_outgoing_lanes = g_macro_link_list[node.m_outgoing_link_list[0]].number_of_lanes if node.m_outgoing_link_list else 0
        self.x = node.x
        self.y = node.y
        self.Initialization()
        
    def Initialization(self):
        global g_number_of_zones
        self.zone_id = g_number_of_zones
        g_number_of_zones += 1
    
    
def GetNetwork():
    import osmnx as ox
    global node_attributes_list
    global link_attributes_list
    global g_macro_node_list
    global g_macro_link_list
    
    node_column_name = ['osmid','x','y']
    link_column_name = ['geometry','highway','lanes','length','maxspeed','name','oneway','osmid','u','v']
    
    G = ox.graph_from_place(city, network_type='drive')
    #G_projected = ox.project_graph(G)
    #ox.plot_graph(G_projected)
    node_attributes_df = ox.graph_to_gdfs(G, edges=False)
    link_attributes_df = ox.graph_to_gdfs(G, nodes=False)    
    node_attributes_column_name = list(node_attributes_df.columns)
    link_attributes_column_name = list(link_attributes_df.columns)
    node_column_index = [node_attributes_column_name.index(el) for el in node_column_name]
    link_column_index = [link_attributes_column_name.index(el) for el in link_column_name]
    node_attributes_df_useful = node_attributes_df.iloc[:,node_column_index]
    link_attributes_df_useful = link_attributes_df.iloc[:,link_column_index]
    
    link_attributes_df_useful['highway'] = link_attributes_df_useful.apply(lambda x: x['highway'][0] if isinstance(x['highway'],list) else x['highway'],axis=1)
    link_attributes_df_useful['osmid'] = link_attributes_df_useful.apply(lambda x: x['osmid'][0] if isinstance(x['osmid'],list) else x['osmid'],axis=1)
    link_attributes_df_useful['lanes'] = link_attributes_df_useful.apply(lambda x: x['lanes'][0] if isinstance(x['lanes'],list) else x['lanes'],axis=1)
    link_attributes_df_useful['maxspeed'] = link_attributes_df_useful.apply(lambda x: x['maxspeed'][0] if isinstance(x['maxspeed'],list) else x['maxspeed'],axis=1)
    
    node_attributes_list = node_attributes_df_useful.values.tolist()
    link_attributes_list = link_attributes_df_useful.values.tolist()  
    
    g_macro_node_list = [MacroNode(*el) for el in node_attributes_list]
    for el in link_attributes_list:
        if el[6]:
            g_macro_link_list.append(MacroLink(*el))
        else:
            g_macro_link_list.append(MacroLink(*(el[:7]+[str(el[7])+'a']+el[8:])))
            g_macro_link_list.append(MacroLink(*(el[:7]+[str(el[7])+'b']+[el[9],el[8]])))


def LonLat2Mile(lon1,lat1,lon2,lat2):
    lonrad1 = lon1 * np.pi / 180
    latrad1 = lat1 * np.pi / 180
    lonrad2 = lon2 * np.pi / 180
    latrad2 = lat2 * np.pi / 180
    
    a = latrad1 - latrad2
    b = lonrad1 - lonrad2
    cal = 2 * np.arcsin(np.sqrt((np.sin(a / 2))**2 + 
            np.cos(latrad1) * np.cos(latrad2) * ((np.sin(b / 2))** 2))) * 6378.137
    return cal
                   

def DemandGeneration():
    if demand_generation == 2: return
    global demand_list
    coordinate_list = []
    number_of_outgoging_lanes_list = []
    number_of_incoming_lanes_list = []
    for i in range(g_number_of_macro_nodes):
        p_node = g_macro_node_list[i]
        if len(p_node.m_incoming_link_list)<2 and len(p_node.m_outgoing_link_list)<2:
            p_node.zone_id = g_number_of_zones
            coordinate_list.append([p_node.x,p_node.y])
            g_zone_list.append(Zone(p_node))
            number_of_outgoging_lanes_list.append(g_zone_list[-1].number_of_outgoing_lanes)
            number_of_incoming_lanes_list.append(g_zone_list[-1].number_of_incoming_lanes)
    
    coordinate_array = np.array(coordinate_list)
    number_of_outgoging_lanes_array = np.array(number_of_outgoging_lanes_list)
    number_of_incoming_lanes_array = np.array(number_of_incoming_lanes_list)
    
    demand_list = [['from_zone_id','to_zone_id','number_of_trips_demand_type1']]
    for i in range(g_number_of_zones):
        zone_distance = LonLat2Mile(coordinate_array[i,0],coordinate_array[i,1],coordinate_array[:,0],coordinate_array[:,1])
        demand = zone_distance * number_of_outgoging_lanes_array[i] * number_of_incoming_lanes_array * demand_factor
        for j in range(g_number_of_zones):
            if demand[j]>0: demand_list.append([i,j,int(np.ceil(demand[j]))])
            

def OutputResults():
    with open('input_macro_node.csv', 'w', newline = '') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['name','node_id','zone_id','micro_node_set','control_type',
                         'control_type_name','cycle_length_in_second','x','y','geometry'])
        for i in range(g_number_of_macro_nodes):
            p_node = g_macro_node_list[i]
            line = [p_node.name,p_node.node_id,p_node.zone_id,p_node.micro_node_set,p_node.control_type,
                    p_node.control_type_name,p_node.cycle_length_in_second,p_node.x,p_node.y,p_node.geometry]
            writer.writerow(line)

    with open('input_macro_link.csv', 'w', newline = '') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['name','link_id','link_key','speed_sensor_id','count_sensor_id','from_node_id','to_node_id',
                         'link_type_name','direction','length','number_of_lanes','speed_limit','lane_cap','link_type',
                         'jam_density','wave_speed','demand_type_code','mode_code','network_design_flag','grade','geometry',
                         'original_geometry','map_matching_orientation_code','map_matching_loop_code','additional_lanes_on_left_side',
                         'length_of_left_side_lanes','additional_lanes_on_right_side','length_of_right_side_lanes'])
        for i in range(g_number_of_macro_links):
            p_link = g_macro_link_list[i]
            line = [p_link.name,p_link.link_id,p_link.link_key,p_link.speed_sensor_id,p_link.count_sensor_id,p_link.from_node_id,
                    p_link.to_node_id,p_link.link_type_name,p_link.direction,p_link.length,p_link.number_of_lanes,p_link.speed_limit,
                    p_link.lane_cap,p_link.link_type,p_link.jam_density,p_link.wave_speed,p_link.demand_type_code,p_link.mode_code,
                    p_link.network_design_flag,p_link.grade,p_link.geometry,p_link.original_geometry,p_link.map_matching_orientation_code,
                    p_link.map_matching_loop_code,p_link.additional_lanes_on_left_side,p_link.length_of_left_side_lanes,
                    p_link.additional_lanes_on_right_side,p_link.length_of_right_side_lanes]
            writer.writerow(line)
    
    if demand_generation == 2: return
    with open('input_demand.csv', 'w', newline = '') as outfile:
        writer = csv.writer(outfile)
        number_of_demands = len(demand_list)
        for i in range(number_of_demands): writer.writerow(demand_list[i])
            
    
if __name__ == '__main__':
    GetNetwork()
    DemandGeneration()
    OutputResults()