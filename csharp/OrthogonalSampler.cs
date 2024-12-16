namespace AIprobe;
using Environment = AIprobe.Models.Environment;

public class OrthogonalSampler
{
    /// <summary>
    /// Reduces the sample size of environments using orthogonal sampling.
    /// </summary>
    /// <param name="environments">The list of environments to sample from.</param>
    /// <param name="levels">The number of levels for orthogonal sampling (e.g., 3 for low/medium/high).</param>
    /// <returns>A reduced list of environments representing a diverse subset.</returns>
    public static List<Environment> ReduceSampleSize(List<Environment> environments, int levels)
    {
        if (environments == null || environments.Count == 0)
            throw new ArgumentException("Environments list cannot be null or empty.");

        if (levels <= 0)
            throw new ArgumentException("Levels must be greater than 0.");

        // Step 1: Convert environments to parameter space
        List<EnvironmentParameters> parameterSpace = environments.Select(env => new EnvironmentParameters
        {
            NameIndex = Math.Abs(env.Name?.GetHashCode() ?? 0) % levels,
            TypeIndex = MapTypeToIndex(env.Type, levels),
            AgentCountIndex = Math.Min(env.Agents.AgentList?.Count() ?? 0, levels - 1),
            ObjectCountIndex = Math.Min(env.Objects.ObjectList?.Count() ?? 0, levels - 1),
            AttributeCountIndex = Math.Min(env.Attributes?.Count ?? 0, levels - 1)
        }).ToList();

        // Step 2: Generate the orthogonal array
        List<int[]> orthogonalArray = GenerateOrthogonalArray(factors: 2, levels: levels);
        Console.WriteLine("Generated Orthogonal Array:");
        foreach (var row in orthogonalArray)
        {
            Console.WriteLine(string.Join(",", row));
        }
        // Step 3: Map orthogonal array to environments
        List<Environment> reducedSample = new List<Environment>();
        
        Console.WriteLine("Parameter Space:");
        foreach (var param in parameterSpace)
        {
            Console.WriteLine($"NameIndex: {param.NameIndex}, TypeIndex: {param.TypeIndex}, AgentCountIndex: {param.AgentCountIndex}, ObjectCountIndex: {param.ObjectCountIndex}, AttributeCountIndex: {param.AttributeCountIndex}");
        }
        
        foreach (var row in orthogonalArray)
        {
            // Find an environment matching this row in the orthogonal array
            var matchedIndex = parameterSpace.FindIndex(p =>
                p.AgentCountIndex == row[0] &&
                p.ObjectCountIndex == row[1] &&
                p.AttributeCountIndex == row[2]);

            if (matchedIndex != -1)
            {
                reducedSample.Add(environments[matchedIndex]);
                parameterSpace.RemoveAt(matchedIndex); // Avoid duplicates
                environments.RemoveAt(matchedIndex); // Keep lists in sync
            }
        }

        return reducedSample;
    }

    /// <summary>
    /// Maps environment type to an index.
    /// </summary>
    private static int MapTypeToIndex(string type, int levels)
    {
        // Example mapping; replace with actual mapping logic
        Dictionary<string, int> typeMapping = new Dictionary<string, int>
        {
            { "TypeA", 0 },
            { "TypeB", 1 },
            { "TypeC", 2 }
        };

        return typeMapping.ContainsKey(type) ? typeMapping[type] % levels : 0;
    }

    private static List<int[]> GenerateOrthogonalArray(int factors, int levels)
    {
        List<int[]> orthogonalArray = new List<int[]>();

        int rows = (int)Math.Pow(levels, factors - 1); // Number of rows

        for (int i = 0; i < rows; i++)
        {
            int[] row = new int[factors];
            for (int j = 0; j < factors; j++)
            {
                row[j] = (i / (int)Math.Pow(levels, j)) % levels;
            }

            orthogonalArray.Add(row);
        }

        return orthogonalArray;
    }
}

public class EnvironmentParameters
{
    public int NameIndex { get; set; }
    public int TypeIndex { get; set; }
    public int AgentCountIndex { get; set; }
    public int ObjectCountIndex { get; set; }
    public int AttributeCountIndex { get; set; }
}
