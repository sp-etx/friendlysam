    ### Compute district heating demand

    # Q_t = b + h_t
    # Q*_t = b + h*_t
    # require that
    # sum_t Q*_t = T * b + sum_t h*_t = k * sum_t Q_t = k * b * T + k * sum_t h_t
    # and require that
    # h*_t = c * h_t
    # ==>
    # b * T * (1 - k) = sum_t (h_t - h*_t) = (k - c) * sum_t h_t
    # ==>
    # c = k - b * T * (1 - k) / sum_t h_t = k - b * (1 - k) / mean(h_t)

    k = parameters['dh_rel_demand']
    b = parameters['dh_base'] * parameters['time_res']
    h = heat_history.sum(axis=1) - b
    c = k - b * (1. - k) / h.mean()
    dh_demand = b + c * h


    