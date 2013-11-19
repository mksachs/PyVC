from pyvc import *
from pyvc import vcutils
from operator import itemgetter
import networkx as nx
from subprocess import call
import cPickle
import sys
import numpy as np
import matplotlib.pyplot as mplt
import itertools

#-------------------------------------------------------------------------------
# Prints out various information about a simulation.
#-------------------------------------------------------------------------------
def sim_info(sim_file, sortby='event_magnitude', show=50, event_range=None, section_filter=None, magnitude_filter=None):
     with VCSimData() as sim_data:
        # open the simulation data file
        sim_data.open_file(sim_file)

        # instantiate the vc classes passing in an instance of the VCSimData
        # class
        events = VCEvents(sim_data)
        geometry = VCGeometry(sim_data)

        event_data = events.get_event_data(['event_number', 'event_year', 'event_magnitude', 'event_range_duration'], event_range=event_range, magnitude_filter=magnitude_filter, section_filter=section_filter)
        
        print '{0:<10}{1:<10}{2:<10}'.format('num','year','magnitude')
        if sortby == 'event_elements':
            sorted_data = [i[0] for i in sorted(enumerate(event_data[sortby]), lambda a,b: cmp(len(b[1]),len(a[1])), reverse=True)][0:show]
        else:
            sorted_data = [i[0] for i in sorted(enumerate(event_data[sortby]), key=itemgetter(1), reverse=True)][0:show]
     
        for i in sorted_data:
            print '{ev_num:<10}{ev_year:<10.2f}{ev_mag:<10.2f}'.format(ev_num=event_data['event_number'][i], ev_year=event_data['event_year'][i], ev_mag=event_data['event_magnitude'][i])

def graph_events(sim_file, output_file, event_range=None, section_filter=None, magnitude_filter=None):
    
    sys.stdout.write('Initializing graph :: ')
    sys.stdout.flush()
    
    with VCSimData() as sim_data:
        # open the simulation data file
        sim_data.open_file(sim_file)

        # instantiate the vc classes passing in an instance of the VCSimData
        # class
        events = VCEvents(sim_data)
        geometry = VCGeometry(sim_data)
        
        # get the data
        event_data = events.get_event_data(['event_elements', 'event_year', 'event_magnitude', 'event_number'], event_range=event_range, magnitude_filter=magnitude_filter, section_filter=section_filter)
        
        # initilize a graph
        G = nx.DiGraph(sim_file=sim_file, event_range=None, section_filter=None, magnitude_filter=None)
        
        sys.stdout.write('{} events : {} years\n'.format(len(event_data['event_year']),event_data['event_year'][-1] - event_data['event_year'][0] ))
        sys.stdout.flush()
        
        # add edges and nodes to the graph for each event
        for i, ev_eles in enumerate(event_data['event_elements']):
            if i%round(float(len(event_data['event_year']))/100.0) == 0:
                sys.stdout.write('\r event {} of {}'.format(i, len(event_data['event_year'])))
                sys.stdout.flush()
            for this_sid in geometry.sections_with_elements(ev_eles):
                try:
                    for next_sid in geometry.sections_with_elements(event_data['event_elements'][i+1]):
                        duration = event_data['event_year'][i+1] - event_data['event_year'][i]
                        try:
                            G[this_sid][next_sid]['weight'] += 1
                            G[this_sid][next_sid]['duration'].append(duration)
                        except KeyError:
                            G.add_edge(this_sid, next_sid, weight=1, duration=[duration])
                        G.node[this_sid]['magnitude'] = event_data['event_magnitude'][i]
                        G.node[this_sid]['number'] = event_data['event_number'][i]
                except IndexError:
                    pass
    
        # add the duration mean and standard deviation
        for i in G:
            for j in G[i]:
                G[i][j]['duration_mean'] = np.mean(G[i][j]['duration'])
                G[i][j]['duration_std'] = np.std(G[i][j]['duration'])

        # save the graph
        sys.stdout.write('\nSaving graph ')
        sys.stdout.flush()
        cPickle.dump(G, open(output_file, 'wb'))

def event_sequence_r(sid, matrix, pos_sid, sid_pos, depth, results, stack, top):
    indices =  (np.argsort(matrix[sid_pos[sid], :]).T)[::-1][0:top]
    
    depth -= 1
    
    stack.append(sid)
    
    
    if depth >= 0:
        
        for i in indices:
            
            event_sequence_r( pos_sid[i[0,0]], matrix, pos_sid, sid_pos, depth, results, stack, top)
        stack.pop()
    else:
        for i in stack:
            results.append(i)
        stack.pop()

def sequence_probability(sequence, matrix, sid_pos):
    
    ret = 1
    
    for i in range(sequence.size):
        try:
            ret *= matrix[sid_pos[sequence[i]], sid_pos[sequence[i+1]]]
        except IndexError:
            pass

    return ret

def event_sequence(graph_file, start_sid, length, top=3):
    G = cPickle.load(open(graph_file, 'rb'))
    
    matrix, pos_sid = nx.attr_matrix(G, edge_attr='weight', normalized=True)
    
    sid_pos = {sid: position for (position, sid) in enumerate(pos_sid)}
    
    results = []
    event_sequence_r(start_sid, matrix, pos_sid, sid_pos, length, results, [], top)
    
    _results = np.reshape(np.array(results), (-1, length+1))
    
    for i in range(_results.shape[0]):
        print _results[i], sequence_probability(_results[i], matrix, sid_pos)
    
    #print _results[0]
    #print len(results), _results.shape, _results.size
    #indices =  (np.argsort(matrix[start_sid, :]).T)[::-1][0:3]
    #print indices[::-1]
    #for i in indices:
    #    print i[0,0]
    
    #for i in itertools.permutations(order,length):
    #    print i
    #print node_map
    '''
    my_matrix = np.zeros((len(G), len(G)))
    
    node_map = {node: key for (key, node) in enumerate(G)}
    #for i, node in enumerate(G):
    
    for i, node in enumerate(G):
        for sid, info in G[node].iteritems():
            j = node_map[sid]
            my_matrix[i,j] = info['weight']
    
    n1 = 10
    n2 = 10
    
    total_weights = 0
    for sid, info in G[n1].iteritems():
        total_weights += info['weight']
    
    print my_matrix[n1, n2], matrix[n1, n2], total_weights
    '''
    '''
    for node in G:
        print node,
        for neighbor in G[node]:
            print neighbor,
        print
    '''
    
    
    #print '11,10', matrix[11, 10]
    #print '10,11', matrix[10, 11]
    #print order
    
    #it = np.nditer(matrix[start_sid, 0:20], flags=['c_index'])
    #while not it.finished:
    #    print it.index, order[it.index], it[0]
    #    it.iternext()
    '''
    # plot parameters
    imw = 1024.0 # the full image width
    imh = 1024.0
    lm = 40.0
    rm = 50.0
    tm = 50.0
    bm = 50.0
    res = 72.0
    cbh = 20.0
    cbs = 40.0
    
    #arial14 = mpl.font_manager.FontProperties(family='Arial', style='normal', variant='normal', size=14)
    #arial12 = mpl.font_manager.FontProperties(family='Arial', style='normal', variant='normal', size=12)
    #arial10 = mpl.font_manager.FontProperties(family='Arial', style='normal', variant='normal', size=10)
    #arial7_light = mpl.font_manager.FontProperties(family='Arial', style='normal', variant='normal', size=7, weight='light')
    
    imwi = imw/res
    imhi = imh/res
    fig = mplt.figure(figsize=(imwi, imhi), dpi=res)
    ph = imh - tm - bm - cbh - cbs # the height for both matricies
    pw = imw - lm - rm
    shear_ax = fig.add_axes((lm/imw, (bm+cbh+cbs)/imh, pw/imw, ph/imh))
    
    shear_ax.imshow(matrix.T, interpolation='none')
    #shear_ax.axis('tight')
    #shear_ax.set_ylim((15.5, 0.5))
    #shear_ax.set_xlim((0.5, 15.5))
    '''
    
    
    '''
    fig.savefig('local/graph_matrix.png', format='png')
    '''
    '''
    total_weights = 0
    for sid, info in G[start_sid].iteritems():
        total_weights += info['weight']
    
    for sid, info in G[start_sid].iteritems():
        print sid, float(info['weight'])/float(total_weights), np.mean(info['duration']), np.std(info['duration']), start_sid
    '''

