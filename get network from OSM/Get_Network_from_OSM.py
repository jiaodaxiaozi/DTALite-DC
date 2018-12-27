# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 12:44:27 2018

@author: Jiawei Lu
"""


units = 1   #1:km,km/h;2:mile,mph
city = 'haidian district, beijing'

g_number_of_macro_nodes = 0
g_number_of_macro_links = 0
node_attributes_list = []
link_attributes_list = []
g_macro_node_list = []
g_macro_link_list = []


class MacroNode:
    def __init__(self,osmid,x,y):
        self.name = ''
        self.node_id = int(osmid)
        self.zone_id = ''
        self.micro_node_set = ''
        self.control_type = ''
        self.control_type_name = ''
        self.cycle_length_in_second = ''
        self.x = x
        self.y = y
        self.geometry = '<Point><coordinates>'+str(x)+','+str(y)+'</coordinates></Point>'
        self.Initialization()
        
    def Initialization(self):
        global g_number_of_macro_nodes
        g_number_of_macro_nodes += 1

class MacroLink:
    def __init__(self,geometry,lanes,length,maxspeed,name,oneway,osmid,u,v):
        self.name = name
        self.link_id = osmid
        self.link_key = ''
        self.speed_sensor_id = ''
        self.count_sensor_id = ''
        self.from_node_id = u
        self.to_node_id = v
        self.link_type_name = ''
        self.direction = 1 if oneway else 2
        self.length = float(length)/1000 if units == 1 else float(length)/1000*0.6214
        if lanes != lanes:
            self.number_of_lanes = -1
        elif isinstance(lanes,str):
            self.number_of_lanes = int(lanes)
        else:
            self.number_of_lanes = int(lanes[0])
            
        if maxspeed != maxspeed:
            self.speed_limit = -1
        else:
            speed_str = maxspeed if isinstance(maxspeed,str) else maxspeed[0]
            if (units == 1) and ('mph' not in speed_str):
                self.speed_limit = float(speed_str)
            elif (units == 1) and ('mph' in speed_str):
                self.speed_limit = float(speed_str[:-4])*1.61
            elif (units == 2) and ('mph' not in speed_str):
                self.speed_limit = float(speed_str)/1.61
            else:
                self.speed_limit = float(speed_str[:-4])
            
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
        g_number_of_macro_links += 1

    
def GetNetwork():
    import osmnx as ox
    global node_attributes_list
    global link_attributes_list
    global g_macro_node_list
    global g_macro_link_list
    
    node_column_name = ['osmid','x','y']
    link_column_name = ['geometry','lanes','length','maxspeed','name','oneway','osmid','u','v']
    
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
    
    node_attributes_list = node_attributes_df_useful.values.tolist()
    link_attributes_list = link_attributes_df_useful.values.tolist()
    g_macro_node_list = [MacroNode(*el) for el in node_attributes_list]
    g_macro_link_list = [MacroLink(*el) for el in link_attributes_list]

def OutputResults():
    import csv
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
            
if __name__ == '__main__':
    GetNetwork()
    OutputResults()