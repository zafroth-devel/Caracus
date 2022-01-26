proposed_edge_key_dict = {}
item_number = 0
for itm in proposed_edges:
    proposed_edge_key_dict[item_number] = itm
    item_number=item_number+1

current_edge_key_dict = {}
item_number = 0
for itm in current_edges:
    current_edge_key_dict[item_number] = itm
    item_number=item_number+1

matched_edges_current = []
matched_edges_proposed = []
for x,y in itertools.product(list(current_edge_key_dict),list(proposed_edge_key_dict)):
    if current_edge_key_dict[x]['from']==proposed_edge_key_dict[y]['from'] and current_edge_key_dict[x]['to']==proposed_edge_key_dict[y]['to']:
        print('{0},{1} matched'.format(x,y))
        matched_edges_current.append(x)
        matched_edges_proposed.append(y)