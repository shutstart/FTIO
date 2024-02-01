from ftio.ioparse.bandwidth import Bandwidth


class Sample:
    """contains metrics for a single I/O type (read/write + async/sync)
    """

    def __init__(self, values, io_type, args):
        self.type                        = io_type
        self.total_bytes                 = self.assign(values,"total_bytes")
        self.max_bytes_per_rank          = self.assign(values,"max_bytes_per_rank")
        #self.max_offset_over_ranks       = self.assign(values,"max_offset_over_ranks")
        self.max_transfersize_over_ranks = self.assign(values,"max_transfersize_over_ranks")
        self.max_io_phases_per_rank      = self.assign(values,"max_io_phases_per_rank")
        self.total_io_phases             = self.assign(values,"total_io_phases")
        self.max_io_ops_in_phase         = self.assign(values,"max_io_ops_in_phase")
        self.max_io_ops_per_rank         = self.assign(values,"max_io_ops_per_rank")
        self.total_io_ops                = self.assign(values,"total_io_ops")
        self.number_of_ranks             = self.assign(values,"number_of_ranks")
        self.bandwidth                   = Bandwidth(values["bandwidth"], io_type, args)
        self.file_index                  = args.file_index

    def get_data(self):
        #! append list is much faster than appen data frame
        name0 = []
        data0 = []
        common        = ['number_of_ranks','file_index']
        name_rank_ovr = ['b_overlap_sum','b_overlap_avr', 't_overlap']
        name_rank     = ['b_rank_sum', 'b_rank_avr', 't_rank_s', 't_rank_e']
        name_ind_ovr  = ['b_overlap_ind', 't_overlap_ind']
        name_ind      = [ 'b_ind', 't_ind_s','t_ind_e']


        # add phase statistics
        for attr, value in self.__dict__.items():
            if (attr not in ['bandwidth', 'file_index']):
                name0.append(attr)
                data0.append(value)

        # statisitcs:
        name_tmp = common + name_rank_ovr + name_rank + name_ind_ovr + name_ind
        for attr, value in self.bandwidth.__dict__.items():
            if (attr not in name_tmp):
                name0.append(attr)
                data0.append(value)

        name_rank_ovr, data1 = self.find_data(name_rank_ovr,common)
        name_rank,     data2 = self.find_data(name_rank,common)
        name_ind_ovr,  data3 = self.find_data(name_ind_ovr,common)
        name_ind,      data4 = self.find_data(name_ind,common)

        return name0, [data0], name_rank_ovr, data1, name_rank, data2, name_ind_ovr, data3, name_ind, data4


    def assign(self,values, name):
        if name in values:
            return values[name]
        else:
            return float('NaN')

    def find_data(self,name,common):
        #remove empty:
        for i in name:
            if not getattr(self.bandwidth,i):
                name.remove(i)

        # add phase info
        data = [getattr(self.bandwidth,s) for s in name]
        l = len(data[-1])
        name = name + common
        data.extend([[self.number_of_ranks]*l,[self.file_index]*l])
        return name, data