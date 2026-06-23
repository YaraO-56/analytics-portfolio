class DataStandardizer:
    def __init__(self, dataframe, mapping_results, target_columns):
        self.dataframe = dataframe.copy()
        self.mapping_results = mapping_results
        self.target_columns = target_columns

    def build_rename_map(self):
        rename_map = {}

        for item in self.mapping_results:
            source = item["source_column"]
            target = item["suggested_target"]

            if target is not None:
                rename_map[source] = target

        return rename_map

    def standardize_columns(self, keep_extra_columns=True):
        rename_map = self.build_rename_map()

        standardized_df = self.dataframe.rename(columns=rename_map)

        for column in self.target_columns:
            if column not in standardized_df.columns:
                standardized_df[column] = None

        extra_columns = [
            col for col in standardized_df.columns
            if col not in self.target_columns
        ]

        if keep_extra_columns:
            final_columns = self.target_columns + extra_columns
        else:
            final_columns = self.target_columns

        standardized_df = standardized_df[final_columns]

        return standardized_df