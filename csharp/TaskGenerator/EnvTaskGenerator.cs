using AIprobe.Logging;
using AIprobe.Models;
using Environment = AIprobe.Models.Environment;
using Attribute = AIprobe.Models.Attribute;
using Object = AIprobe.Models.Object;

namespace AIprobe.TaskGenerator
{
    public class EnvTaskGenerator
    {
        // private Random random;
        //
        // // Constructor with seed parameter
        // public EnvTaskGenerator(int seed)
        // {
        //     random = new Random(seed); 
        // }
        //
        // /// <summary>
        // /// Generate various tasks based on the environment within the given time
        // /// </summary>
        // /// <param name="environmentConfig">environment config object</param>
        // /// <param name="timeLimitInSeconds">time</param>
        // /// <returns></returns>
        // public List<(AIprobe.Models.Environment,Environment)> GenerateTasks(Environment environmentConfig,
        //     int timeLimitInSeconds)
        // {
        //     Console.WriteLine(random.Next()); 
        //     
        //     
        //     List<(AIprobe.Models.Environment,Environment)> tasks = new List<(AIprobe.Models.Environment,Environment)>();
        //     DateTime startTime = DateTime.Now;
        //
        //     Logger.LogInfo($"Task generation started with a time limit of {timeLimitInSeconds} seconds.");
        //     var totalMutableAttributes = 0;
        //     int taskCount = 0;
        //     while ((DateTime.Now - startTime).TotalSeconds < timeLimitInSeconds)
        //     {
        //         AIprobe.Models.Environment initialState = Program.DeepCopy(environmentConfig);
        //         //AIprobe.Models.Environment finalState = Program.DeepCopy(environmentConfig);
        //         
        //         // gentrating new initial state
        //         MutateAgentProperties(initialState);
        //         MutateObjectProperties((initialState));
        //
        //         AIprobe.Models.Environment finalState = Program.DeepCopy(initialState);
        //         MutateAgentProperties(finalState);
        //         //MutateObjectProperties((finalState));
        //         tasks.Add((initialState, finalState));
        //     }
        //
        //     Logger.LogInfo(
        //         $"Task generation completed. {tasks.Count} tasks were generated within {timeLimitInSeconds} seconds.");
        //     return tasks;
        // }
        //
        //
        // /// <summary>
        // /// This method processes the mutable properties of agents within the environment.
        // /// It selects random mutable attributes and modifies them accordingly.
        // /// </summary>
        // /// <param name="environmentConfig"></param>
        // /// <returns></returns>
        // private Environment MutateAgentProperties(Environment environmentConfig){
        //     var mutableAttributes = ProcessAgentListForMutableAttributes(environmentConfig.Agents.AgentList);
        //     
        //     Dictionary<string, List<string>> selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);
        //     
        //     ModifyMutableAttributes(environmentConfig.Agents.AgentList, mutableAttributes);
        //
        //     return environmentConfig;
        //     
        // }
        //
        // /// <summary>
        // /// Processes a list of agents and identifies mutable attributes.
        // /// </summary>
        // /// <param name="agentList">The list of agents to process.</param>
        // /// <returns>
        // /// A dictionary where the key is the agent's ID , and the value is a list of mutable attribute names for that agent.
        // /// </returns>
        // private Dictionary<string, List<string>> ProcessAgentListForMutableAttributes(List<AIprobe.Models.Agent> agentList)
        // {
        //     Dictionary<string, List<string>> agentMutableAttributes = new Dictionary<string, List<string>>();
        //
        //     foreach (var agent in agentList)
        //     {
        //         List<string> mutableAttributeNames = new List<string>();
        //
        //         // Process Position attributes
        //         foreach (var attr in agent.Position.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         // Process Direction attributes
        //         foreach (var attr in agent.Direction.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         // If there are mutable attributes, add them to the dictionary with the agent's ID
        //         if (mutableAttributeNames.Count > 0)
        //         {
        //             agentMutableAttributes[agent.Id.ToString()] = mutableAttributeNames;
        //         }
        //     }
        //
        //     return agentMutableAttributes; // Return the dictionary with agent ID and mutable attribute names
        // }
        //
        // /// <summary>
        // /// Randomly selects a subset of values from each key's list in the provided dictionary. 
        // /// </summary>
        // /// <param name="attributesDictionary">
        // /// A dictionary where the key is eithe agent id or object id  and the value  is a list of mutable attribute names associated with that entity.
        // /// </param>
        // /// <returns>
        // /// A dictionary where the key is eithe agent id or object id  and the value is a random list of mutable attribute names associated with that entity.
        // /// </returns>
        // private Dictionary<string, List<string>> RandomlySelectValuesFromDictionary(Dictionary<string, List<string>> attributesDictionary)
        // {
        //     Random random = new Random();
        //     Dictionary<string, List<string>> selectedValuesDictionary = new Dictionary<string, List<string>>();
        //
        //     // Iterate over each key in the dictionary
        //     foreach (var entry in attributesDictionary)
        //     {
        //         string key = entry.Key;  // The key (Agent or Object ID)
        //         List<string> values = entry.Value;  // The list of mutable attribute names for this key
        //
        //         if (values.Count == 0)
        //         {
        //             // If there are no values for this key, skip
        //             continue;
        //         }
        //
        //         // Randomly decide how many values to select for this key (between 1 and the total number of values)
        //         int numberToSelect = random.Next(1, values.Count + 1);
        //
        //         List<string> selectedValues = new List<string>();
        //
        //         // Randomly select unique values
        //         while (selectedValues.Count < numberToSelect)
        //         {
        //             int index = random.Next(0, values.Count);  // Random index
        //             string selectedValue = values[index];
        //
        //             if (!selectedValues.Contains(selectedValue))  // Ensure no duplicates
        //             {
        //                 selectedValues.Add(selectedValue);
        //             }
        //         }
        //
        //         // Add the selected values to the result dictionary
        //         selectedValuesDictionary[key] = selectedValues;
        //     }
        //
        //     return selectedValuesDictionary;
        // }
        //
        //
        // /// <summary>
        // /// Modifies the mutable attributes for a list of agents based on the provided dictionary of mutable attributes.
        // /// </summary>
        // /// <param name="agentList">The list of agents to process for mutable attributes.</param>
        // /// <param name="mutableAttributes">
        // /// A dictionary where the key is the agent's id, and the value is a list of mutable attribute names that should be modified for that agent.
        // /// </param>
        // private void ModifyMutableAttributes(List<AIprobe.Models.Agent> agentList, Dictionary<string, List<string>> mutableAttributes)
        // {
        //     foreach (var agent in agentList)
        //     {
        //         if (mutableAttributes.ContainsKey(agent.Id.ToString()))
        //         {
        //             // Get the mutable attribute names for this agent
        //             List<string> attributesToMutate = mutableAttributes[agent.Id.ToString()];
        //
        //             // Modify Position attributes and store the selected values
        //             ModifyEntityAttributes(agent.Position.Attributes, attributesToMutate);
        //
        //             // Modify Direction attributes and store the selected values
        //             ModifyEntityAttributes(agent.Direction.Attributes, attributesToMutate);
        //         }
        //     }
        // }
        //
        //
        // /// <summary>
        // /// This method processes the mutable properties of objects within the environment.
        // /// It selects random mutable attributes and modifies them accordingly.
        // /// </summary>
        // /// <param name="environmentConfig"></param>
        // /// <returns></returns>
        // private Environment MutateObjectProperties(Environment environmentConfig){
        //     var mutableAttributes = ProcessObjectListForMutableAttributes(environmentConfig.Objects.ObjectList);
        //         
        //     // Randomly select indices from mutable attributes
        //     Dictionary<string, List<string>> selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);
        //     
        //     ModifyMutableAttributes(environmentConfig.Objects.ObjectList, mutableAttributes);
        //
        //     return environmentConfig;
        //     
        // }
        //
        //
        // /// <summary>
        // /// process object list and gather mutable attribute names
        // /// </summary>
        // /// <param name="objectList"></param>
        // /// <returns></returns>
        // private Dictionary<string, List<string>> ProcessObjectListForMutableAttributes(List<AIprobe.Models.Object> objectList)
        // {
        //     Dictionary<string, List<string>> objectMutableAttributes = new Dictionary<string, List<string>>();
        //
        //     foreach (var obj in objectList)
        //     {
        //         List<string> mutableAttributeNames = new List<string>();
        //
        //         // if (obj.Type != "interactive")
        //         // {
        //         //      continue;
        //         // }
        //         
        //         // Process Object attributes
        //         foreach (var attr in obj.ObjectAttributes.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         foreach (var attr in obj.Position.Attributes)
        //         {
        //             if (attr.Mutable?.Value == true)
        //             {
        //                 mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
        //             }
        //         }
        //
        //         // If there are mutable attributes, add them to the dictionary with the object's ID
        //         if (mutableAttributeNames.Count > 0)
        //         {
        //             objectMutableAttributes[obj.Id.ToString()] = mutableAttributeNames;
        //         }
        //     }
        //
        //     return objectMutableAttributes; // Return the dictionary with object ID and mutable attribute names
        // }
        //
        //
        // /// <summary>
        // /// Modify mutable attributes for Objects,based on the dictionary of mutable attributes
        // /// </summary>
        // /// <param name="objectList"></param>
        // /// <param name="mutableAttributes"></param>
        // private void ModifyMutableAttributes(List<AIprobe.Models.Object> objectList, Dictionary<string, List<string>> mutableAttributes)
        // {
        //     foreach (var obj in objectList)
        //     {
        //         if (mutableAttributes.ContainsKey(obj.Id.ToString()))
        //         {
        //             // Get the mutable attribute names for this object
        //             List<string> attributesToMutate = mutableAttributes[obj.Id.ToString()];
        //             
        //             ModifyEntityAttributes(obj.Position.Attributes, attributesToMutate);
        //
        //             // Modify Object attributes and store the selected values
        //             ModifyEntityAttributes(obj.ObjectAttributes.Attributes, attributesToMutate);
        //         }
        //     }
        // }
        //
        //
        // /// <summary>
        // /// to modify entity attributes (used by both Agent and Object) and store selected values
        // /// </summary>
        // /// <param name="attributes"></param>
        // /// <param name="attributesToMutate"></param>
        // private void ModifyEntityAttributes(List<AIprobe.Models.Attribute> attributes, List<string> attributesToMutate)
        // {
        //     foreach (var attr in attributes)
        //     {
        //         // Check if this attribute's name is in the list of names to mutate
        //         if (attributesToMutate.Contains(attr.Name.Value))
        //         {
        //             // Apply changes to the attribute
        //             var newValue = ChangeAttributeValue(attr); // Example of modifying the attribute value
        //     
        //             // Assign the mutated value back to the attribute
        //             attr.Value.ValueData = newValue.ToString();
        //         }
        //     }
        // }
        //
        //
        // /// <summary>
        // /// Randomly change the value of the attribute based on the data type
        // /// </summary>
        // /// <param name="attr">atributes of the agent or object</param>
        // /// <returns>Modified value of the attribute</returns>
        // private object ChangeAttributeValue(AIprobe.Models.Attribute attr)
        // {
        //     Random random = new Random();
        //
        //     // Change the value based on the data type
        //     if (attr.DataType.Value == "int")
        //     {
        //      
        //         
        //         // Example: Random integer value between Min and Max
        //         return random.Next(Convert.ToInt32(attr.Min.Value), Convert.ToInt32(attr.Max.Value));
        //     }
        //     else if (attr.DataType.Value == "float")
        //     {
        //         // Example: Random float value between Min and Max
        //         return (float)(random.NextDouble() * (Convert.ToSingle(attr.Max.Value) - Convert.ToSingle(attr.Min.Value)) + Convert.ToSingle(attr.Min.Value));
        //     }
        //     else if (attr.DataType.Value == "string")
        //     {
        //         // If it's a string, randomly select from the ValueList
        //         if (attr.ValueList != null && attr.ValueList.Pairs != null && attr.ValueList.Pairs.Count > 0)
        //         {
        //             // Randomly select a Pair from the ValueList
        //             int randomIndex = random.Next(0, attr.ValueList.Pairs.Count);
        //             return attr.ValueList.Pairs[randomIndex].Value; // Return the value from the selected pair
        //         }
        //     }
        //     else if (attr.DataType.Value == "bool")
        //     {
        //         // Randomly assign true or false for boolean type
        //         return random.Next(0, 2) == 0; // 50% chance of true or false
        //     }
        //
        //     // Default: return the original value if no change is needed
        //     return attr.Value.ValueData;
        // }
        //

        public static List<Environment> TaskGenerator(Environment baseEnv,double envcount, int? seed = null)
        {
            // Step 1: Resolve constraints only for mutable attributes
            var (independentRanges, dependentConstraints, dataTypes) = ResolveMutableConstraints(baseEnv);

            // Determine the number of samples based on the ranges and constraints
            int nSamples = (independentRanges.Count + dependentConstraints.Count) * 10;

            // Step 2: Perform LHS sampling with dependencies
            var sampledValues = LhsSampler.PerformLhsWithDependencies(independentRanges, dependentConstraints, nSamples,
                    seed);

            // Step 3: Save sampled values to CSV (optional)
            //SaveToCsv(sampledValues, $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/{envcount}/sampled_Taskvalues.csv");

            // Step 4: Generate environments based on the sampled values
            var sampledEnvironments = new List<Environment>();
            foreach (var sample in sampledValues)
            {
                var newEnv = CloneEnvironment(baseEnv); // Clone the base environment
                ApplySamplesToEnvironment(newEnv, sample, dataTypes);
                
                sampledEnvironments.Add(newEnv);
            }

            return sampledEnvironments;
        }

        /// <summary>
        /// Resolves constraints for attributes marked as mutable.
        /// </summary>
       private static (Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
    Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints,
    List<string> dataTypes)
ResolveMutableConstraints(Environment baseEnv)
{
    var independentRanges = new Dictionary<string, (double Min, double Max, string DataType)>();
    var dependentConstraints = new Dictionary<string, (string MinExpr, string MaxExpr, string DataType)>();
    var dataTypes = new List<string>();

    // Process global attributes
    foreach (var attr in baseEnv.Attributes.Where(attr => attr.Mutable.Value))
    {
        string attrName = attr.Name.Value;
        string minExpr = attr.Constraint.Min ?? "0";
        string maxExpr = attr.Constraint.Max ?? "0";
        string dataType = attr.DataType.Value;

        if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
        {
            independentRanges[attrName] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
        }
        else
        {
            string strippedMinExpr = StripBraces(minExpr);
            string strippedMaxExpr = StripBraces(maxExpr);

            dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr, DataType: dataType);
        }

        dataTypes.Add(dataType);
    }

    // Process agent attributes
    foreach (var agent in baseEnv.Agents.AgentList)
    {
        foreach (var attr in agent.Attributes.Where(attr => attr.Mutable.Value))
        {
            string key = $"Agent_{agent.Id}_{attr.Name.Value}";
            string minExpr = attr.Constraint.Min ?? "0";
            string maxExpr = attr.Constraint.Max ?? "0";
            string dataType = attr.DataType.Value;

            if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
            {
                independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
            }
            else
            {
                string strippedMinExpr = StripBraces(minExpr);
                string strippedMaxExpr = StripBraces(maxExpr);

                dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr, DataType: dataType);
            }

            dataTypes.Add(dataType);
        }
    }

    // Process object attributes
    foreach (var obj in baseEnv.Objects.ObjectList)
    {
        foreach (var attr in obj.Attributes.Where(attr => attr.Mutable.Value))
        {
            string key = $"Object_{obj.Id}_{attr.Name.Value}";
            string minExpr = attr.Constraint.Min ?? "0";
            string maxExpr = attr.Constraint.Max ?? "0";
            string dataType = attr.DataType.Value;

            if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
            {
                independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
            }
            else
            {
                string strippedMinExpr = StripBraces(minExpr);
                string strippedMaxExpr = StripBraces(maxExpr);

                dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr, DataType: dataType);
            }

            dataTypes.Add(dataType);
        }
    }

    return (independentRanges, dependentConstraints, dataTypes);
}

        private static string StripBraces(string expression)
        {
            if (expression.StartsWith("{") && expression.EndsWith("}"))
            {
                return expression.Substring(1, expression.Length - 2); // Remove the leading and trailing braces
            }

            return expression;
        }
        
        /// <summary>
        /// Applies sampled values to environment attributes.
        /// </summary>
        private static void ApplySamplesToEnvironment(Environment env, Dictionary<string, double> sample,
            List<string> dataTypes)
        {
            int dataTypeIndex = 0;

            foreach (var attr in env.Attributes.Where(attr => attr.Mutable.Value))
            {
                if (sample.ContainsKey(attr.Name.Value))
                {
                    attr.Value.Content = Convert.ToString(sample[attr.Name.Value]);
                    attr.DataType.Value = dataTypes.ElementAtOrDefault(dataTypeIndex++) ?? attr.DataType.Value;
                }
            }
            
            
            
            foreach (var agent in env.Agents.AgentList)
            {
                foreach (var attr in agent.Attributes)
                {
                    string sampleKey = $"Agent_{agent.Id}_{attr.Name.Value}";
                    if (sample.ContainsKey(sampleKey))
                    {
                        attr.Value.Content = Convert.ToString(sample[sampleKey]);
                        attr.DataType.Value = dataTypes.ElementAtOrDefault(dataTypeIndex++) ?? attr.DataType.Value;
                    }
                }
            }

           
        }

// Utility methods: CloneEnvironment, SaveToCsv, AdjustObjectsGlobally, StripBraces, and others are reused as needed.


// Generic function to collect mutable attributes
        private static void CollectMutableAttributes(
            Environment baseEnv,
            List<Attribute> mutableAttributes,
            List<string> dataTypes,
            List<double[]> resolvedParams,
            Dictionary<int, Func<double[], double>> dependencies)
        {
            int index = 0;

            // Collect attributes from global scope
            CollectAttributes(baseEnv.Attributes, mutableAttributes, dataTypes, resolvedParams, dependencies,
                ref index);

            // Collect attributes from agents
            foreach (var agent in baseEnv.Agents.AgentList)
            {
                CollectAttributes(agent.Attributes, mutableAttributes, dataTypes, resolvedParams, dependencies,
                    ref index);
            }

            // Collect attributes from objects
            foreach (var obj in baseEnv.Objects.ObjectList)
            {
                CollectAttributes(obj.Attributes, mutableAttributes, dataTypes, resolvedParams, dependencies,
                    ref index);
            }
        }

// Generic function to process attributes and handle constraints/dependencies
        private static void CollectAttributes(
            List<Attribute> attributes,
            List<Attribute> mutableAttributes,
            List<string> dataTypes,
            List<double[]> resolvedParams,
            Dictionary<int, Func<double[], double>> dependencies,
            ref int index)
        {
            foreach (var attr in attributes)
            {
                if (attr.Mutable?.Value == true && attr.Constraint != null)
                {
                    mutableAttributes.Add(attr);
                    dataTypes.Add(attr.DataType.Value);

                    // Parse Min and Max constraints
                    double min = ResolveExpression(attr.Constraint.Min, dependencies, index);
                    double max = ResolveExpression(attr.Constraint.Max, dependencies, index);

                    resolvedParams.Add(new double[] { min, max });
                    index++;
                }
            }
        }

// Resolve constraints dynamically
        private static double ResolveExpression(string expression, Dictionary<int, Func<double[], double>> dependencies,
            int index)
        {
            if (string.IsNullOrEmpty(expression))
            {
                return 0; // Default to 0 if no constraint is defined
            }

            if (expression.Contains("{") && expression.Contains("}"))
            {
                // Parse dependency and add to the dictionary
                string dependency = expression.Trim('{', '}');
                dependencies[index] = (sample) =>
                {
                    // Resolve the dependency dynamically (e.g., "Grid - 1")
                    var tokens = dependency.Split(' ');
                    double result = double.Parse(tokens[0]); // Example for "Grid - 1"
                    if (tokens.Length > 2 && tokens[1] == "-")
                    {
                        result -= double.Parse(tokens[2]);
                    }

                    return result;
                };

                // Return a placeholder; the actual value will be resolved dynamically during sampling
                return 0;
            }

            // Direct numeric value
            return double.Parse(expression);
        }

// Deep copy the environment
        private static Environment CloneEnvironment(Environment env)
        {
            return new Environment
            {
                Name = env.Name,
                Type = env.Type,
                Attributes = new List<Attribute>(env.Attributes.Select(attr => new Attribute
                {
                    Name = attr.Name,
                    DataType = attr.DataType,
                    Value = new Value { Content = attr.Value.Content },
                    Constraint = attr.Constraint,
                    Mutable = attr.Mutable
                })),
                Agents = new Agents
                {
                    AgentList = env.Agents.AgentList.ConvertAll(agent => new Agent
                    {
                        Id = agent.Id,
                        Type = agent.Type,
                        Attributes = agent.Attributes.Select(attr => new Attribute
                        {
                            Name = attr.Name,
                            DataType = attr.DataType,
                            Value = new Value { Content = attr.Value.Content },
                            Constraint = attr.Constraint,
                            Mutable = attr.Mutable
                        }).ToList()
                    })
                },
                Objects = new Objects
                {
                    ObjectList = env.Objects.ObjectList.ConvertAll(obj => new Object
                    {
                        Id = obj.Id,
                        Type = obj.Type,
                        Attributes = obj.Attributes.Select(attr => new Attribute
                        {
                            Name = attr.Name,
                            DataType = attr.DataType,
                            Value = new Value { Content = attr.Value.Content },
                            Constraint = attr.Constraint,
                            Mutable = attr.Mutable
                        }).ToList()
                    })
                }
            };
        }
        
        
        
        private static void SaveToCsv(List<Dictionary<string, double>> sampledValues, string filePath)
        {
            // Open a file stream and write the CSV content
            using (var writer = new System.IO.StreamWriter(filePath))
            {
                if (sampledValues.Count > 0)
                {
                    // Write the header row (keys of the dictionary)
                    var headers = string.Join(",", sampledValues[0].Keys);
                    writer.WriteLine(headers);

                    // Write each sample row (values of the dictionary)
                    foreach (var sample in sampledValues)
                    {
                        var row = string.Join(",",
                            sample.Values.Select(value =>
                                value.ToString(System.Globalization.CultureInfo.InvariantCulture)));
                        writer.WriteLine(row);
                    }
                }
            }
        }
    }
}