using System.Data;
using AIprobe.Logging;
using AIprobe.Models;
using AIprobe.Parsers;
using Attribute = AIprobe.Models.Attribute;
using Environment = AIprobe.Models.Environment;
using Object = AIprobe.Models.Object;

namespace AIprobe.EnvironmentGenerator
{
    public class EnvConfigGenerator
    {
        
        public static List<Environment> GenerateEnvConfigs(Environment baseEnv, int nSamples)
        {
            // Step 1: Resolve constraints
            var (resolvedParams, dataTypes) = ResolveConstraintsAsVector(baseEnv); // Updated to unpack the tuple

            // Step 2: Perform LHS sampling
            var sampledEnvironments = LhsSampler.PerformLhsSamplingAsVector(resolvedParams, nSamples, dataTypes); // Pass dataTypes

            // Step 3: Generate sampled environments
            var sampledEnvironmentsList = new List<Environment>();

            foreach (var sample in sampledEnvironments)
            {
                var newEnv = CloneEnvironment(baseEnv); // Clone the base environment to avoid overwriting
                ApplySamplesToEnvironmentAsVector(newEnv, new List<double[]> { sample }); // Pass dataTypes here
                sampledEnvironmentsList.Add(newEnv);
                
                
                // Print all attribute values in the new environment
                Console.WriteLine($"Environment: {newEnv.Name}, Type: {newEnv.Type}");

                // Print global attributes
                Console.WriteLine("Global Attributes:");
                foreach (var attr in newEnv.Attributes)
                {
                    Console.WriteLine($"  {attr.Name.Value}: {attr.Value.Content}");
                }

                // Print agent attributes
                Console.WriteLine("Agents:");
                foreach (var agent in newEnv.Agents.AgentList)
                {
                    Console.WriteLine($"  Agent ID: {agent.Id}");
                    foreach (var attr in agent.Attributes)
                    {
                        Console.WriteLine($"    {attr.Name.Value}: {attr.Value.Content}");
                    }
                }

                // Print object attributes
                Console.WriteLine("Objects:");
                foreach (var obj in newEnv.Objects.ObjectList)
                {
                    Console.WriteLine($"  Object ID: {obj.Id}");
                    foreach (var attr in obj.Attributes)
                    {
                        Console.WriteLine($"    {attr.Name.Value}: {attr.Value.Content}");
                    }
                }

                Console.WriteLine();
            }

            return sampledEnvironmentsList;
        }

        
    //     public static List<Environment> GenerateEnvConfigs(Environment baseEnv, int nSamples)
    // {
    //     // Step 1: Resolve constraints
    //     //var resolvedParams = ResolveConstraints(baseEnv);
    //     
    //     var resolvedParam = ResolveConstraintsAsVector(baseEnv);
    //
    //     // Step 2: Perform LHS sampling
    //     //var lhsSamples = LhsSampler.PerformLhsSampling(resolvedParams, nSamples);
    //     
    //     
    //     var sampledEnvironmentss = LhsSampler.PerformLhsSamplingAsVector(resolvedParam, nSamples);
    //
    //     
    //     // Step 3: Generate sampled environments
    //     var sampledEnvironments = new List<Environment>();
    //     
    //     // Step 3: Apply the samples to the environment
    //     foreach (var sample in sampledEnvironmentss)
    //     {
    //         ApplySamplesToEnvironmentAsVector(baseEnv, new List<double[]> { sample });
    //         sampledEnvironments.Add(baseEnv);
    //     }
    //     
    //    
    //     // foreach (var sample in lhsSamples)
    //     // {
    //     //     var newEnv = CloneEnvironment(baseEnv);
    //     //     ApplySamplesToEnvironment(newEnv, sample);
    //     //     sampledEnvironments.Add(newEnv);
    //     // }
    //
    //     return sampledEnvironments;
    // }

    private static Environment CloneEnvironment(Environment env)
    {
        // Perform a deep copy of the environment
        return new Environment
        {
            Name = env.Name,
            Type = env.Type,
            Attributes = new List<Attribute>(env.Attributes),
            Agents = new Agents
            {
                AgentList = env.Agents.AgentList.ConvertAll(agent => new Agent
                {
                    Id = agent.Id,
                    Attributes = new List<Attribute>(agent.Attributes)
                })
            },
            Objects = new Objects
            {
                ObjectList = env.Objects.ObjectList.ConvertAll(obj => new Object
                {
                    Id = obj.Id,
                    Attributes = new List<Attribute>(obj.Attributes)
                })
            }
        };
    }

    
    
    
    
    
 public static (double[,], List<string>) ResolveConstraintsAsVector(Environment env)
{
    int paramCount = env.Attributes.Count + 
                     (env.Agents?.AgentList?.Sum(agent => agent.Attributes?.Count ?? 0) ?? 0) + 
                     (env.Objects?.ObjectList?.Sum(obj => obj.Attributes?.Count ?? 0) ?? 0);

    double[,] resolvedParams = new double[paramCount, 2];
    List<string> dataTypes = new List<string>(); // To track data types for each parameter

    var context = new Dictionary<string, double>();
    int index = 0;

    // Add global attributes with "global" context
    index = ResolveAttributeConstraintsAsVector(env.Attributes, resolvedParams, dataTypes, context, index, "");

    // Add agent attributes with "agent,<id>" context
    foreach (var agent in env.Agents?.AgentList ?? new List<Agent>())
    {
        string agentContext = $"agent,{agent.Id}";
        index = ResolveAttributeConstraintsAsVector(agent.Attributes, resolvedParams, dataTypes, context, index, agentContext);
    }

    // Add object attributes with "object,<id>" context
    foreach (var obj in env.Objects?.ObjectList ?? new List<Object>())
    {
        string objectContext = $"object,{obj.Id}";
        index = ResolveAttributeConstraintsAsVector(obj.Attributes, resolvedParams, dataTypes, context, index, objectContext);
    }

    return (resolvedParams, dataTypes); // Return both resolved constraints and data types
}

private static int ResolveAttributeConstraintsAsVector(
    List<Attribute> attributes,
    double[,] resolvedParams,
    List<string> dataTypes,
    Dictionary<string, double> context,
    int index,
    string parentContext)
{
    foreach (var attr in attributes)
    {
        // Construct a unique context path
        string contextPath = $"{parentContext},{attr.Name.Value}";
        if (parentContext == "")
        {
            contextPath = attr.Name.Value;
        }

        // Replace placeholders with actual values in the context
        var minExpr = attr.Constraint.Min?.Replace("{", "").Replace("}", "") ?? "0";
        var maxExpr = attr.Constraint.Max?.Replace("{", "").Replace("}", "") ?? "0";

        if (string.IsNullOrEmpty(minExpr) || string.IsNullOrEmpty(maxExpr))
        {
            dataTypes.Add(attr.DataType.Value);
            continue;
        }

        // Evaluate Min and Max using the context
        double minValue = EvaluateExpression(minExpr, context);
        double maxValue = EvaluateExpression(maxExpr, context);

        // Store resolved values
        resolvedParams[index, 0] = minValue;
        resolvedParams[index, 1] = maxValue;

        // Track the data type of the attribute
        dataTypes.Add(attr.DataType.Value); // Assuming `DataType` contains the type (e.g., "int", "float")

        // Update the context dictionary with the resolved value
        if (double.TryParse(attr.Value.Content, out var currentValue))
        {
            context[contextPath] = currentValue; // Use contextPath as the key
        }

        index++;
    }

    return index;
}
    
private static void ApplySamplesToEnvironmentAsVector(Environment env, List<double[]> samples)
{
    int sampleIndex = 0;

    // Apply sampled values to global attributes
    foreach (var attr in env.Attributes)
    {
        attr.Value.Content = samples[0][sampleIndex].ToString(); // Assign sampled value as-is
        sampleIndex++;
    }

    // Apply sampled values to agent attributes
    foreach (var agent in env.Agents.AgentList)
    {
        foreach (var attr in agent.Attributes)
        {
            attr.Value.Content = samples[0][sampleIndex].ToString(); // Assign sampled value as-is
            sampleIndex++;
        }
    }

    // Apply sampled values to object attributes
    foreach (var obj in env.Objects.ObjectList)
    {
        foreach (var attr in obj.Attributes)
        {
            attr.Value.Content = samples[0][sampleIndex].ToString(); // Assign sampled value as-is
            sampleIndex++;
        }
    }
}
    
    private static void ApplySamplesToEnvironment(Environment env, Dictionary<string, double> sample)
    {
        // Apply to global attributes
        ApplySamplesToAttributes(env.Attributes, sample);

        // Apply to agent attributes
        foreach (var agent in env.Agents.AgentList)
        {
            ApplySamplesToAttributes(agent.Attributes, sample);
        }

        // Apply to object attributes
        foreach (var obj in env.Objects.ObjectList)
        {
            ApplySamplesToAttributes(obj.Attributes, sample);
        }
    }

    private static void ApplySamplesToAttributes(List<Attribute> attributes, Dictionary<string, double> sample)
    {
        foreach (var attr in attributes)
        {
            if (sample.ContainsKey(attr.Name.Value))
            {
                attr.Value.Content = sample[attr.Name.Value].ToString("F2");
            }
        }
    }

    public static Dictionary<string, (double Min, double Max)> ResolveConstraints(Environment env)
    {
        var resolvedParams = new Dictionary<string, (double Min, double Max)>();
        var context = new Dictionary<string, double>();

        // Parse global attributes
        foreach (var attr in env.Attributes)
        {
            AddAttributeToContext(attr, context);
        }

        // Parse agent attributes
        foreach (var agent in env.Agents.AgentList)
        {
            foreach (var attr in agent.Attributes)
            {
                AddAttributeToContext(attr, context);
            }
        }

        // Parse object attributes
        foreach (var obj in env.Objects.ObjectList)
        {
            foreach (var attr in obj.Attributes)
            {
                AddAttributeToContext(attr, context);
            }
        }

        // Resolve constraints for all attributes
        ResolveAttributeConstraints(env.Attributes, resolvedParams, context);

        foreach (var agent in env.Agents.AgentList)
        {
            ResolveAttributeConstraints(agent.Attributes, resolvedParams, context);
        }

        foreach (var obj in env.Objects.ObjectList)
        {
            ResolveAttributeConstraints(obj.Attributes, resolvedParams, context);
        }

        return resolvedParams;
    }

    private static void AddAttributeToContext(Attribute attr, Dictionary<string, double> context)
    {
        if (double.TryParse(attr.Value.Content, out var val))
        {
            context[attr.Name.Value] = val;
        }
    }

    private static void ResolveAttributeConstraints(List<Attribute> attributes, Dictionary<string, (double Min, double Max)> resolvedParams, Dictionary<string, double> context)
    {
        foreach (var attr in attributes)
        {
            var minExpr = attr.Constraint.Min?.Replace("{", "").Replace("}", "") ?? "0";
            var maxExpr = attr.Constraint.Max?.Replace("{", "").Replace("}", "") ?? "0";

            if (minExpr == null || maxExpr == null || minExpr == "" || maxExpr == "")
            {
                continue;
            }
            var minValue = EvaluateExpression(minExpr, context);
            var maxValue = EvaluateExpression(maxExpr, context);

            resolvedParams[attr.Name.Value] = (minValue, maxValue);
            context[attr.Name.Value] = maxValue;
        }
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
}

        
        
        
        
        
        
        
        // /// <summary>
        // /// Generate various env based on the initial environment provide by user.
        // /// </summary>
        // /// <param name="initialEnvironment">initial env object</param>
        // /// <returns>list of mutated env object</returns>
        // public List<AIprobe.Models.Environment> GenerateEnvConfigs(Environment initialEnvironment, int seed)
        // {
        //     Random random = new Random(seed);
        //     List<AIprobe.Models.Environment> environments = new List<Environment>();
        //     
        //     
        //     int randomNumberOfEnviroment = random.Next(1, 13);
        //
        //     Logger.LogInfo($"Environment generation started.");
        //
        //
        //     environments = hardCodedEnvironments(initialEnvironment);
        //    
        //     //0,0
        //     
        //     
        //
        //     
        //     
        //     
        //     // for (int i = 0; i < randomNumberOfEnviroment-2; i++)  // Generate 10 random environments
        //     // {
        //     //     // Deep copy the initial environment to preserve the original state for each iteration
        //     //     Environment initialEnvironmentCopy = Program.DeepCopy(initialEnvironment);
        //     //     List<int> objectIdList = CheckNameTagsMatch(initialEnvironmentCopy);
        //     //
        //     //     // Loop through the objects in the environment and mutate based on random number for that environment
        //     //     foreach (int objectId in objectIdList)
        //     //     {
        //     //         // Random number for the action (add/remove object)
        //     //         int randomNumber = random.Next(0, 2);
        //     //         //Console.WriteLine($"Random number for object {objectId} in environment {i + 1}: {randomNumber}");
        //     //
        //     //         if (randomNumber == 1)
        //     //         {
        //     //             // Add a new object
        //     //             AddNewObject(initialEnvironmentCopy);
        //     //         }
        //     //         else
        //     //         {
        //     //             // Remove an object
        //     //             RemoveObjectById(initialEnvironmentCopy, objectId);
        //     //         }
        //     //       
        //     //     }
        //     //     
        //     //     
        //     //
        //     //     // Add the mutated environment to the list
        //     //     environments.Add(initialEnvironmentCopy);
        //     //     Logger.LogInfo($"Environment {i + 1} generation completed.");
        //     // }
        //     //
        //     //
        //     
        //     // 
        //     
        //
        //     Logger.LogInfo("All environments generated successfully.");
        //     return environments;
        // }
        //
        //
        //
        // private List<AIprobe.Models.Environment>  hardCodedEnvironments(AIprobe.Models.Environment environments)
        // {
        //     //0,0
        //     List<AIprobe.Models.Environment> environmentsList = new List<Environment>();
        //     
        //     // Get all XML files from the specified directory
        //     string[] xmlFiles = Directory.GetFiles(Program.testingHardCoddedEnvs, "*.xml");
        //
        //     if (xmlFiles.Length == 0)
        //     {
        //         Logger.LogError("No XML files found in the specified directory.");
        //         return environmentsList; // Return an empty list if no XML files are found
        //     }
        //     
        //     
        //     foreach (var filePath in xmlFiles)
        //     {
        //         EnvironmentParser initialParser = new EnvironmentParser(filePath);
        //         AIprobe.Models.Environment initialEnvironment = initialParser.ParseEnvironment();
        //
        //         // You can now mutate or modify the initialEnvironment as needed
        //         // For example, you can deep copy it and generate variations
        //
        //         // Add the initial environment (parsed from XML) to the environments list
        //         environmentsList.Add(initialEnvironment);
        //         Logger.LogInfo($"Parsed environment from file: {filePath}");
        //     }
        //     
        //     Logger.LogInfo($"Edge case environment with 0 objects added.");
        //     
        //     
        //     return environmentsList;
        //     
        // }
        //
        // /// <summary>
        // /// Adds a new object to the environment.
        // /// </summary>
        // /// <param name="environmentConfig">The environment configuration to modify</param>
        // /// <summary>
        // /// Adds a new object to the environment by finding an existing object with the same name and only changing its Id.
        // /// </summary>
        // /// <param name="environmentConfig">The environment configuration to modify</param>
        // private void AddNewObject(Environment environmentConfig)
        // {
        //     // Find an object with the same name (can be the first match or a random one)
        //     var existingObject = environmentConfig.Objects.ObjectList
        //         .OrderBy(_ => Guid.NewGuid()) // Shuffle the list to randomly pick one
        //         .FirstOrDefault(obj => obj.Name == "ObjectNameYouAreMatching"); // Replace with the actual matching condition
        //
        //     if (existingObject == null)
        //     {
        //         Logger.LogError("No matching object found to copy from.");
        //         return; // Exit if no matching object is found
        //     }
        //
        //     // Create a new object by copying properties from the found object and assigning a new Id
        //     var newObject = new AIprobe.Models.Object
        //     {
        //         Id = environmentConfig.Objects.ObjectList.Max(obj => obj.Id) + 1, // Generate a new Id
        //         Name = existingObject.Name,  // Keep the same name as the found object
        //         Position = existingObject.Position,
        //         ObjectAttributes = existingObject.ObjectAttributes
        //         
        //         // Copy other relevant properties as needed
        //     };
        //
        //     environmentConfig.Objects.ObjectList.Add(newObject);
        //     Logger.LogInfo($"Added new object with Id: {newObject.Id}, copied from object with Id: {existingObject.Id}");
        // }
        //
        //
        // /// <summary>
        // /// Removes an object from the environment based on its Id.
        // /// </summary>
        // /// <param name="environmentConfig">The environment configuration to modify</param>
        // /// <param name="objectId">The Id of the object to remove</param>
        // private void RemoveObjectById(Environment environmentConfig, int objectId)
        // {
        //     var objectToRemove = environmentConfig.Objects.ObjectList
        //         .FirstOrDefault(obj => obj.Id == objectId);
        //     if (objectToRemove != null)
        //     {
        //         environmentConfig.Objects.ObjectList.Remove(objectToRemove);
        //         Logger.LogInfo($"Removed object with Id: {objectId}");
        //     }
        // }
        //
        //
        //
        //
        // /// <summary>
        // /// Checks if the name tags of environment properties and object names match.
        // /// </summary>
        // /// <param name="environmentConfig">The environment configuration object containing agents and objects.</param>
        // /// <returns>A list of tuples indicating whether names match and their corresponding names.</returns>
        // public List<int> CheckNameTagsMatch(Environment environmentConfig)
        // {
        //     var results = new List<int>();
        //
        //     // Check names of agents in the environment
        //
        //     // Check names of objects in the environment
        //     foreach (var obj in environmentConfig.Objects.ObjectList)
        //     {
        //         // Assuming object has a property Name
        //         string objectName = obj.Name;
        //
        //         // Compare object names with environment property names
        //         bool isMatch = environmentConfig.Objects.ObjectList
        //             .Any(agent => agent.Name == objectName);
        //
        //         foreach (var env in environmentConfig.EnvironmentalProperties.Properties)
        //         {
        //             if (env.Name == objectName)
        //             {
        //                 results.Add(obj.Id);
        //             }
        //             
        //         }
        //         
        //         //bool isInProperties = environmentConfig.EnvironmentalProperties.PropertiesContains(objectName);
        //
        //        ; // Agent names are null for this case
        //     }
        //
        //     Logger.LogInfo("Checked name tags for agents and objects.");
        //     return results;
        // }

    
    }


