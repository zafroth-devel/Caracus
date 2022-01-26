from intervaltree import Interval, IntervalTree
def parse_intervals(intergrp):

    # All incremental dates are related to this one
    basedate = intergrp[0].min_h_start_date
    buid = intergrp[0].hierarchy_bu_id
    resources = intergrp[0].resources

    # Load interval tree
    itree = IntervalTree()

    for itm in intergrp: 
        itree[itm.incremental_start:itm.incremental_start+itm.total_days+1] = {'cid':itm.change_group_id,'res':itm.resources,'req':itm.required} 
    
    # Need to create contiguous intervals tied to length and number of resources
    all_data = []
    for itm in itree:
        begin = itm.begin
        end = itm.end
        data = itm.data
        cycle = begin
        split_interval = []
        # Remove the interval we are currently looking at
        itree.removei(begin, end, data)
        while True:
            # Start cycle
            if cycle == begin:
                interval_list = [cycle]

            # Test current and next 
            test1 = sorted(itree[cycle])
            test2 = sorted(itree[cycle+1])

            if test1 != test2 or (cycle+1 == end and len(interval_list)==1):
                interval_list.append(cycle)
                interval_list.append([itms.data['req'] for itms in test1])
                split_interval.append(interval_list)
                interval_list = [cycle+1]

            if cycle+1 == end:
                break

            cycle = cycle + 1
        
        # Add the interval back in 
        itree[begin:end] = data

        # Workon the split
        for cnts in split_interval:
            denom = sum(cnts[2])
            total = data['req']+denom
            if total > resources:
                # Modify output
                mod = resources/total
                ndenom = [float(i)*mod for i in denom]
                score = (float(data['req'])*mod)/(resources-sum(ndenom))
            else:
                score = data['req']/(resources-denom)
            cnts.append(round(score,2))
            cnts[0] = basedate+timedelta(days=cnts[0])
            cnts[1] = basedate+timedelta(days=cnts[1])

        # Append scores to list and continue (not done yet)
        all_data.append({data['cid']:split_interval})

    return {'all_data':all_data,'itree':itree}

#geo = parse_intervals(incremental_src)