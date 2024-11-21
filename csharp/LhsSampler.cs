namespace AIprobe;

public class LhsSampler
{
    public static List<Dictionary<string, double>> PerformLhsSampling(Dictionary<string, (double Min, double Max)> resolvedParams, int nSamples)
    {
        var random = new Random();
        var samples = new List<Dictionary<string, double>>();
        var paramKeys = resolvedParams.Keys.ToList();
        var dim = resolvedParams.Count;
        var lhsMatrix = new double[nSamples, dim];

        // Generate LHS matrix
        for (int i = 0; i < dim; i++)
        {
            var intervals = Enumerable.Range(0, nSamples)
                .Select(j => (j + random.NextDouble()) / nSamples)
                .OrderBy(x => x)
                .ToArray();

            for (int j = 0; j < nSamples; j++)
            {
                lhsMatrix[j, i] = intervals[j];
            }
        }

        // Scale LHS samples to parameter ranges
        for (int i = 0; i < nSamples; i++)
        {
            var sample = new Dictionary<string, double>();
            for (int j = 0; j < dim; j++)
            {
                var param = paramKeys[j];
                var range = resolvedParams[param];
                sample[param] = lhsMatrix[i, j] * (range.Max - range.Min) + range.Min;
            }
            samples.Add(sample);
        }

        return samples;
    }
    
    
    public static List<double[]> PerformLhsSamplingAsVector(double[,] resolvedParams, int nSamples, List<string> dataTypes)
    {
        int paramCount = resolvedParams.GetLength(0); // Number of parameters (dimensions)
        var random = new Random();
        var samples = new List<double[]>();

        // Create LHS intervals for each parameter
        double[,] lhsMatrix = new double[nSamples, paramCount];

        for (int j = 0; j < paramCount; j++)
        {
            double minValue = resolvedParams[j, 0];
            double maxValue = resolvedParams[j, 1];
            double intervalWidth = (maxValue - minValue) / nSamples;

            // Generate intervals for the parameter
            var intervals = Enumerable.Range(0, nSamples)
                .Select(i => minValue + i * intervalWidth)
                .ToList();

            // Shuffle intervals
            intervals = intervals.OrderBy(_ => random.Next()).ToList();

            // Assign a random value within each interval
            for (int i = 0; i < nSamples; i++)
            {
                lhsMatrix[i, j] = intervals[i] + random.NextDouble() * intervalWidth;
            }
        }

        // Convert LHS matrix to a list of samples
        for (int i = 0; i < nSamples; i++)
        {
            var sample = new double[paramCount];

            for (int j = 0; j < paramCount; j++)
            {
                // Adjust the sample based on the data type
                if (dataTypes[j] == "int")
                {
                    sample[j] = Math.Round(lhsMatrix[i, j]); // Convert to an integer
                }
                else if (dataTypes[j] == "float")
                {
                    sample[j] = lhsMatrix[i, j]; // Keep as a float
                }
            }

            samples.Add(sample);
        }

        return samples;
    }
    
    
}