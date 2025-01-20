using System.Data;

namespace AIprobe;

public class LhsSampler
{
    public static List<Dictionary<string, double>> PerformLhsWithDependencies(
            Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints,
            int nSamples,
            int? seed = null)
        {
            var random = seed.HasValue ? new Random(seed.Value) : new Random();

            // Step 1: Initialize stratified intervals for independent parameters
            var stratifiedIntervals = new Dictionary<string, List<double>>();
            foreach (var (key, (minValue, maxValue, dataType)) in independentRanges)
            {
                double intervalWidth = (maxValue - minValue) / nSamples;

                // Create stratified intervals
                var intervals = Enumerable.Range(0, nSamples)
                    .Select(i => minValue + i * intervalWidth)
                    .OrderBy(_ => random.Next()) // Shuffle intervals
                    .ToList();

                stratifiedIntervals[key] = intervals;
            }

            // Step 2: Generate LHS samples for independent parameters
            var lhsSamples = new List<Dictionary<string, double>>();
            for (int i = 0; i < nSamples; i++)
            {
                var sample = new Dictionary<string, double>();

                // Sample independent parameters
                foreach (var (key, (minValue, maxValue, dataType)) in independentRanges)
                {
                    double intervalStart = stratifiedIntervals[key][i];
                    double intervalWidth = (maxValue - minValue) / nSamples;
                    double value = intervalStart + random.NextDouble() * intervalWidth;

                    // If the data type is integer, round the value
                    if (dataType.Equals("int", StringComparison.OrdinalIgnoreCase))
                    {
                        value = Math.Round(value);
                    }

                    sample[key] = value;
                }

                lhsSamples.Add(sample);
            }

            // Step 3: Resolve dependent parameters dynamically
            foreach (var (key, (minExpr, maxExpr, dataType)) in dependentConstraints)
            {
                for (int i = 0; i < nSamples; i++)
                {
                    // Evaluate the dependent min and max expressions using the current sample
                    var min = EvaluateExpression(minExpr, lhsSamples[i]);
                    var max = EvaluateExpression(maxExpr, lhsSamples[i]);

                    double intervalWidth = (max - min) / nSamples;

                    // Stratify and sample the dependent parameter
                    double intervalStart = min + i * intervalWidth;
                    double value = intervalStart + random.NextDouble() * intervalWidth;

                    // If the data type is integer, round the value
                    if (dataType.Equals("int", StringComparison.OrdinalIgnoreCase))
                    {
                        value = Math.Round(value);
                    }

                    lhsSamples[i][key] = value;
                }
            }

            return lhsSamples;
        }
    
    
    
    public static List<Dictionary<string, double>> PerformRandomSamplingWithDependencies(
        Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
        Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints,
        int nSamples,
        int? seed = null)
    {
        var random = seed.HasValue ? new Random(seed.Value) : new Random();

        // Step 1: Generate random samples for independent parameters
        var randomSamples = new List<Dictionary<string, double>>();
        for (int i = 0; i < nSamples; i++)
        {
            var sample = new Dictionary<string, double>();

            foreach (var (key, (minValue, maxValue, dataType)) in independentRanges)
            {
                // Randomly pick a value within the range
                double value = minValue + random.NextDouble() * (maxValue - minValue);

                // If the data type is integer, round the value
                if (dataType.Equals("int", StringComparison.OrdinalIgnoreCase))
                {
                    value = Math.Round(value);
                }

                sample[key] = value;
            }

            randomSamples.Add(sample);
        }

        // Step 2: Resolve dependent parameters dynamically
        foreach (var (key, (minExpr, maxExpr, dataType)) in dependentConstraints)
        {
            for (int i = 0; i < nSamples; i++)
            {
                // Evaluate the dependent min and max expressions using the current sample
                var min = EvaluateExpression(minExpr, randomSamples[i]);
                var max = EvaluateExpression(maxExpr, randomSamples[i]);

                // Randomly pick a value within the dependent range
                double value = min + random.NextDouble() * (max - min);

                // If the data type is integer, round the value
                if (dataType.Equals("int", StringComparison.OrdinalIgnoreCase))
                {
                    value = Math.Round(value);
                }

                randomSamples[i][key] = value;
            }
        }

        return randomSamples;
    }


        private static double EvaluateExpression(string expression, Dictionary<string, double> context)
        {
            foreach (var kvp in context)
            {
                expression = expression.Replace(kvp.Key, kvp.Value.ToString());
            }

            var dataTable = new DataTable();
            return Convert.ToDouble(dataTable.Compute(expression, null));
        }

        private static IEnumerable<string> ExtractUnresolvedKeys(string expression)
        {
            var unresolvedKeys = new List<string>();
            int startIndex = expression.IndexOf('{');
            while (startIndex != -1)
            {
                int endIndex = expression.IndexOf('}', startIndex);
                if (endIndex != -1)
                {
                    var key = expression.Substring(startIndex + 1, endIndex - startIndex - 1);
                    unresolvedKeys.Add(key);
                    startIndex = expression.IndexOf('{', endIndex);
                }
                else
                {
                    break; // No matching closing brace
                }
            }

            return unresolvedKeys;
        }
        
        
        
        public static List<Dictionary<string, double>> PerformLhsWithDependenciesImproved(
        Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
        Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints,
        int nSamples,
        int? seed = null)
    {
        var random = seed.HasValue ? new Random(seed.Value) : new Random();

        // Step 1: Initialize stratified intervals for independent parameters
        var stratifiedIntervals = new Dictionary<string, Queue<double>>();
        foreach (var (key, (minValue, maxValue, dataType)) in independentRanges)
        {
            double intervalWidth = (maxValue - minValue) / nSamples;

            // Create stratified intervals
            var intervals = Enumerable.Range(0, nSamples)
                .Select(i => minValue + i * intervalWidth + random.NextDouble() * intervalWidth)
                .OrderBy(_ => random.Next()) // Shuffle intervals
                .ToList();

            stratifiedIntervals[key] = new Queue<double>(intervals); // Use a queue to ensure unique interval usage
        }

        // Step 2: Generate LHS samples for independent parameters
        var lhsSamples = new List<Dictionary<string, double>>();
        for (int i = 0; i < nSamples; i++)
        {
            var sample = new Dictionary<string, double>();

            // Sample independent parameters
            foreach (var (key, (minValue, maxValue, dataType)) in independentRanges)
            {
                double value = stratifiedIntervals[key].Dequeue(); // Dequeue ensures unique interval usage

                // If the data type is integer, round the value
                if (dataType.Equals("int", StringComparison.OrdinalIgnoreCase))
                {
                    value = Math.Round(value);
                }

                sample[key] = value;
            }

            lhsSamples.Add(sample);
        }

        // Step 3: Resolve dependent parameters dynamically
        foreach (var (key, (minExpr, maxExpr, dataType)) in dependentConstraints)
        {
            // Evaluate dependent constraints
            var dependentIntervals = new Queue<double>();
            foreach (var sample in lhsSamples)
            {
                // Evaluate the dependent min and max expressions
                double min = EvaluateExpression(minExpr, sample);
                double max = EvaluateExpression(maxExpr, sample);

                if (min > max)
                {
                    throw new ArgumentException($"Invalid range for dependent parameter '{key}': Min ({min}) > Max ({max}).");
                }

                double intervalWidth = (max - min) / nSamples;

                // Create stratified intervals for the dependent parameter
                var intervals = Enumerable.Range(0, nSamples)
                    .Select(i => min + i * intervalWidth + random.NextDouble() * intervalWidth)
                    .OrderBy(_ => random.Next())
                    .ToList();

                foreach (var interval in intervals)
                {
                    dependentIntervals.Enqueue(interval);
                }
            }

            // Assign dependent values to the samples
            for (int i = 0; i < nSamples; i++)
            {
                double value = dependentIntervals.Dequeue();

                // If the data type is integer, round the value
                if (dataType.Equals("int", StringComparison.OrdinalIgnoreCase))
                {
                    value = Math.Round(value);
                }

                lhsSamples[i][key] = value;
            }
        }

        return lhsSamples;
    }
        
        
        
    public static List<int[]> GenerateLHSSamples(
        int nSamples,
        Dictionary<string, (double Min, double Max)> ranges,
        int? seed = null)
    {
        var random = seed.HasValue ? new Random(seed.Value) : new Random();

        // Step 1: Initialize stratified intervals for each parameter
        var stratifiedIntervals = new Dictionary<string, Queue<double>>();
        foreach (var (key, (minValue, maxValue)) in ranges)
        {
            double intervalWidth = (maxValue - minValue) / nSamples;

            // Create stratified intervals
            var intervals = Enumerable.Range(0, nSamples)
                .Select(i => minValue + i * intervalWidth + random.NextDouble() * intervalWidth)
                .OrderBy(_ => random.Next()) // Shuffle intervals
                .ToList();

            stratifiedIntervals[key] = new Queue<double>(intervals); // Use a queue to ensure unique interval usage
        }

        // Step 2: Generate LHS samples
        var result = new List<int[]>();
        for (int i = 0; i < nSamples; i++)
        {
            var sample = new int[ranges.Count];
            int index = 0;

            foreach (var key in ranges.Keys)
            {
                double value = stratifiedIntervals[key].Dequeue(); // Dequeue ensures unique interval usage
                sample[index++] = (int)Math.Round(value); // Convert to integer
            }

            result.Add(sample);
        }

        return result;
    }

    // private static double EvaluateExpression(string expression, Dictionary<string, double> variables)
    // {
    //     // A placeholder implementation for evaluating mathematical expressions.
    //     // Replace this with a robust library like NCalc, Jace.NET, or any custom logic.
    //     foreach (var (key, value) in variables)
    //     {
    //         expression = expression.Replace(key, value.ToString());
    //     }
    //
    //     // Assuming the expression is a simple mathematical formula that can be evaluated
    //     // safely, this is just a placeholder. For production, use a proper parser.
    //     return Convert.ToDouble(new System.Data.DataTable().Compute(expression, ""));
    // }

        
        
        
    }
    
    
    
    
//     public static List<Dictionary<string, double>> PerformLhsSampling(Dictionary<string, (double Min, double Max)> resolvedParams, int nSamples)
//     {
//         var random = new Random();
//         var samples = new List<Dictionary<string, double>>();
//         var paramKeys = resolvedParams.Keys.ToList();
//         var dim = resolvedParams.Count;
//         var lhsMatrix = new double[nSamples, dim];
//
//         // Generate LHS matrix
//         for (int i = 0; i < dim; i++)
//         {
//             var intervals = Enumerable.Range(0, nSamples)
//                 .Select(j => (j + random.NextDouble()) / nSamples)
//                 .OrderBy(x => x)
//                 .ToArray();
//
//             for (int j = 0; j < nSamples; j++)
//             {
//                 lhsMatrix[j, i] = intervals[j];
//             }
//         }
//
//         // Scale LHS samples to parameter ranges
//         for (int i = 0; i < nSamples; i++)
//         {
//             var sample = new Dictionary<string, double>();
//             for (int j = 0; j < dim; j++)
//             {
//                 var param = paramKeys[j];
//                 var range = resolvedParams[param];
//                 sample[param] = lhsMatrix[i, j] * (range.Max - range.Min) + range.Min;
//             }
//             samples.Add(sample);
//         }
//
//         return samples;
//     }
//     
//     
//     // public static List<double[]> PerformLhsSamplingAsVector(double[,] resolvedParams, int nSamples, List<string> dataTypes)
//     // {
//     //     int paramCount = resolvedParams.GetLength(0); // Number of parameters (dimensions)
//     //     var random = new Random();
//     //     var samples = new List<double[]>();
//     //
//     //     // Create LHS intervals for each parameter
//     //     double[,] lhsMatrix = new double[nSamples, paramCount];
//     //
//     //     for (int j = 0; j < paramCount; j++)
//     //     {
//     //         double minValue = resolvedParams[j, 0];
//     //         double maxValue = resolvedParams[j, 1];
//     //         double intervalWidth = (maxValue - minValue) / nSamples;
//     //
//     //         // Generate intervals for the parameter
//     //         var intervals = Enumerable.Range(0, nSamples)
//     //             .Select(i => minValue + i * intervalWidth)
//     //             .ToList();
//     //
//     //         // Shuffle intervals
//     //         intervals = intervals.OrderBy(_ => random.Next()).ToList();
//     //
//     //         // Assign a random value within each interval
//     //         for (int i = 0; i < nSamples; i++)
//     //         {
//     //             lhsMatrix[i, j] = intervals[i] + random.NextDouble() * intervalWidth;
//     //         }
//     //     }
//     //
//     //     // Convert LHS matrix to a list of samples
//     //     for (int i = 0; i < nSamples; i++)
//     //     {
//     //         var sample = new double[paramCount];
//     //
//     //         for (int j = 0; j < paramCount; j++)
//     //         {
//     //             // Adjust the sample based on the data type
//     //             if (dataTypes[j] == "int")
//     //             {
//     //                 sample[j] = Math.Round(lhsMatrix[i, j]); // Convert to an integer
//     //             }
//     //             else if (dataTypes[j] == "float")
//     //             {
//     //                 sample[j] = lhsMatrix[i, j]; // Keep as a float
//     //             }
//     //         }
//     //
//     //         samples.Add(sample);
//     //     }
//     //
//     //     return samples;
//     // }
//     //
//     
//     
//     
//     /// <summary>
//     /// Performs Latin Hypercube Sampling for an N-dimensional parameter space.
//     /// </summary>
//     /// <param name="paramRanges">A 2D array where each row contains the [min, max] range for a parameter.</param>
//     /// <param name="nSamples">The number of samples to generate.</param>
//     /// <param name="seed">Optional seed for reproducibility.</param>
//     /// <returns>A list of samples, where each sample is an array of values corresponding to the parameters.</returns>
//     public static List<double[]> PerformLhsSamplingAsVector(double[,] paramRanges, int nSamples, int? seed = null)
//     {
//         int nDimensions = paramRanges.GetLength(0); // Number of dimensions
//         var random = seed.HasValue ? new Random(seed.Value) : new Random();
//
//         // Initialize stratified intervals for each dimension
//         var stratifiedIntervals = new List<double[]>();
//         for (int dim = 0; dim < nDimensions; dim++)
//         {
//             double minValue = paramRanges[dim, 0];
//             double maxValue = paramRanges[dim, 1];
//             double intervalWidth = (maxValue - minValue) / nSamples;
//
//             // Create stratified intervals
//             var intervals = Enumerable.Range(0, nSamples)
//                 .Select(i => minValue + i * intervalWidth)
//                 .ToArray();
//
//             // Shuffle intervals randomly
//             intervals = intervals.OrderBy(_ => random.Next()).ToArray();
//             stratifiedIntervals.Add(intervals);
//         }
//
//         // Initialize the LHS matrix
//         var lhsMatrix = new List<double[]>();
//
//         // Generate samples for each stratified interval
//         for (int i = 0; i < nSamples; i++)
//         {
//             var sample = new double[nDimensions];
//             for (int dim = 0; dim < nDimensions; dim++)
//             {
//                 double intervalStart = stratifiedIntervals[dim][i];
//                 double intervalEnd = intervalStart + (paramRanges[dim, 1] - paramRanges[dim, 0]) / nSamples;
//
//                 // Randomly pick a value within the interval
//                 sample[dim] = intervalStart + random.NextDouble() * (intervalEnd - intervalStart);
//             }
//             lhsMatrix.Add(sample);
//         }
//
//         return lhsMatrix;
//     }
//     
//     
//
// public static class LatinHypercubeSampler
// {
//     /// <summary>
//     /// Performs LHS with dynamic dependencies between parameters.
//     /// </summary>
//     /// <param name="independentRanges">Static ranges for independent parameters.</param>
//     /// <param name="dependencies">A dictionary mapping dependent parameters to their dependency functions.</param>
//     /// <param name="nSamples">The number of samples to generate.</param>
//     /// <param name="seed">Optional seed for reproducibility.</param>
//     /// <returns>A list of samples, where each sample is an array of values corresponding to the parameters.</returns>
//     public static List<double[]> PerformLhsWithDependencies(
//         double[,] independentRanges,
//         Dictionary<int, Func<double[], (double Min, double Max)>> dependencies,
//         int nSamples,
//         int? seed = null)
//     {
//         int nIndependent = independentRanges.GetLength(0); // Number of independent parameters
//         int nTotal = nIndependent + dependencies.Count;    // Total number of parameters
//         var random = seed.HasValue ? new Random(seed.Value) : new Random();
//
//         // Initialize stratified intervals for independent parameters
//         var stratifiedIntervals = new List<double[]>();
//         for (int dim = 0; dim < nIndependent; dim++)
//         {
//             double minValue = independentRanges[dim, 0];
//             double maxValue = independentRanges[dim, 1];
//             double intervalWidth = (maxValue - minValue) / nSamples;
//
//             // Create stratified intervals
//             var intervals = Enumerable.Range(0, nSamples)
//                 .Select(i => minValue + i * intervalWidth)
//                 .OrderBy(_ => random.Next())
//                 .ToArray();
//
//             stratifiedIntervals.Add(intervals);
//         }
//
//         // Step 1: Generate LHS samples for independent parameters
//         var lhsMatrix = new List<double[]>();
//         for (int i = 0; i < nSamples; i++)
//         {
//             var sample = new double[nTotal];
//
//             // Sample independent parameters
//             for (int dim = 0; dim < nIndependent; dim++)
//             {
//                 double intervalStart = stratifiedIntervals[dim][i];
//                 double intervalWidth = (independentRanges[dim, 1] - independentRanges[dim, 0]) / nSamples;
//                 sample[dim] = intervalStart + random.NextDouble() * intervalWidth;
//             }
//
//             lhsMatrix.Add(sample);
//         }
//
//         // Step 2: Resolve dependent parameters
//         foreach (var dep in dependencies)
//         {
//             int dependentIndex = dep.Key;
//             var dependencyFunction = dep.Value;
//
//             for (int i = 0; i < nSamples; i++)
//             {
//                 // Resolve range dynamically
//                 var (min, max) = dependencyFunction(lhsMatrix[i]);
//                 double intervalWidth = (max - min) / nSamples;
//
//                 // Stratify and sample the dependent parameter
//                 double intervalStart = min + i * intervalWidth;
//                 lhsMatrix[i][dependentIndex] = intervalStart + random.NextDouble() * intervalWidth;
//             }
//         }
//
//         return lhsMatrix;
//     }
// }
//
//
//
// /// <summary>
//     /// Performs LHS with dynamic dependencies between parameters.
//     /// </summary>
//     /// <param name="independentRanges">Static ranges for independent parameters.</param>
//     /// <param name="dependencies">A dictionary mapping dependent parameters to their dependency functions.</param>
//     /// <param name="nSamples">The number of samples to generate.</param>
//     /// <param name="seed">Optional seed for reproducibility.</param>
//     /// <returns>A list of samples, where each sample is an array of values corresponding to the parameters.</returns>
//     public static List<double[]> PerformLhsWithDependencies(
//         double[,] independentRanges,
//         Dictionary<int, Func<double[], (double Min, double Max)>> dependencies,
//         int nSamples,
//         int? seed = null)
//     {
//         int nIndependent = independentRanges.GetLength(0); // Number of independent parameters
//         int nTotal = nIndependent + dependencies.Count;    // Total number of parameters
//         var random = seed.HasValue ? new Random(seed.Value) : new Random();
//
//         // Initialize stratified intervals for independent parameters
//         var stratifiedIntervals = new List<double[]>();
//         for (int dim = 0; dim < nIndependent; dim++)
//         {
//             double minValue = independentRanges[dim, 0];
//             double maxValue = independentRanges[dim, 1];
//             double intervalWidth = (maxValue - minValue) / nSamples;
//
//             // Create stratified intervals
//             var intervals = Enumerable.Range(0, nSamples)
//                 .Select(i => minValue + i * intervalWidth)
//                 .OrderBy(_ => random.Next())
//                 .ToArray();
//
//             stratifiedIntervals.Add(intervals);
//         }
//
//         // Step 1: Generate LHS samples for independent parameters
//         var lhsMatrix = new List<double[]>();
//         for (int i = 0; i < nSamples; i++)
//         {
//             var sample = new double[nTotal];
//
//             // Sample independent parameters
//             for (int dim = 0; dim < nIndependent; dim++)
//             {
//                 double intervalStart = stratifiedIntervals[dim][i];
//                 double intervalWidth = (independentRanges[dim, 1] - independentRanges[dim, 0]) / nSamples;
//                 sample[dim] = intervalStart + random.NextDouble() * intervalWidth;
//             }
//
//             lhsMatrix.Add(sample);
//         }
//
//         // Step 2: Resolve dependent parameters
//         foreach (var dep in dependencies)
//         {
//             int dependentIndex = dep.Key;
//             var dependencyFunction = dep.Value;
//
//             for (int i = 0; i < nSamples; i++)
//             {
//                 // Resolve range dynamically
//                 var (min, max) = dependencyFunction(lhsMatrix[i]);
//                 double intervalWidth = (max - min) / nSamples;
//
//                 // Stratify and sample the dependent parameter
//                 double intervalStart = min + i * intervalWidth;
//                 lhsMatrix[i][dependentIndex] = intervalStart + random.NextDouble() * intervalWidth;
//             }
//         }
//
//         return lhsMatrix;
//     }
//
//
//
//
//     
//     public static List<double[]> PerformInterdependentLhsSampling(
//     double[,] resolvedParams,
//     int nSamples,
//     List<string> dataTypes,
//     Dictionary<int, Func<double[], double>> dependencies)
// {
//     int paramCount = resolvedParams.GetLength(0); // Number of parameters
//     var random = new Random();
//     var lhsMatrix = new double[nSamples, paramCount];
//
//     // Stratify each parameter's range and adjust for dependencies
//     for (int j = 0; j < paramCount; j++)
//     {
//         var intervals = new double[nSamples];
//         double minValue = resolvedParams[j, 0];
//         double maxValue = resolvedParams[j, 1];
//         double intervalWidth = (maxValue - minValue) / nSamples;
//
//         for (int i = 0; i < nSamples; i++)
//         {
//             intervals[i] = minValue + i * intervalWidth;
//         }
//
//         // Shuffle intervals to ensure randomness
//         intervals = intervals.OrderBy(_ => random.Next()).ToArray();
//
//         for (int i = 0; i < nSamples; i++)
//         {
//             // Adjust maxValue dynamically if there is a dependency
//             if (dependencies.ContainsKey(j))
//             {
//                 // Extract the current sample row up to column j
//                 var currentSample = new double[j];
//                 for (int k = 0; k < j; k++)
//                 {
//                     currentSample[k] = lhsMatrix[i, k];
//                 }
//
//                 // Update maxValue dynamically using the dependency function
//                 maxValue = dependencies[j](currentSample);
//                 intervalWidth = (maxValue - minValue) / nSamples;
//             }
//
//
//             // Sample within the interval
//             lhsMatrix[i, j] = intervals[i] + random.NextDouble() * intervalWidth;
//         }
//     }
//
//     // Convert LHS matrix to list of samples
//     var samples = new List<double[]>();
//     for (int i = 0; i < nSamples; i++)
//     {
//         var sample = new double[paramCount];
//         for (int j = 0; j < paramCount; j++)
//         {
//             // Adjust the sample based on the data type
//             if (dataTypes[j] == "int")
//             {
//                 sample[j] = Math.Round(lhsMatrix[i, j]); // Convert to an integer
//             }
//             else if (dataTypes[j] == "float")
//             {
//                 sample[j] = lhsMatrix[i, j]; // Keep as a float
//             }
//         }
//
//         samples.Add(sample);
//     }
//
//     return samples;
// }

    