using AIprobe.Logging;
using AIprobe.Models;
using Environment = AIprobe.Models.Environment;
using Attribute = AIprobe.Models.Attribute;
using Object = AIprobe.Models.Object;

namespace AIprobe.TaskGenerator
{
    public class EnvTaskGenerator
    {
        Random random = new Random(Aiprobe.seed);

        // private Random random;
        //
        // // Constructor with seed parameter
        // public EnvTaskGenerator(int seed)
        // {
        //     random = new Random(seed); 
        // }
        //
        /// <summary>
        /// Generate various tasks based on the environment within the given time
        /// </summary>
        /// <param name="environmentConfig">environment config object</param>
        /// <param name="timeLimitInSeconds">time</param>
        /// <returns></returns>
        public List<(Environment, Environment)> GenerateTasks(Environment environmentConfig,
            int timeLimitInSeconds)
        {
            List<(AIprobe.Models.Environment, Environment)> tasks =
                new List<(AIprobe.Models.Environment, Environment)>();
            DateTime startTime = DateTime.Now;

            Logger.LogInfo($"Task generation started with a time limit of {timeLimitInSeconds} seconds.");
            Console.WriteLine($"Task generation started with a time limit of {timeLimitInSeconds} seconds.");
            var totalMutableAttributes = 0;
            int taskCount = 0;

            CancellationTokenSource cts = new CancellationTokenSource();
            cts.CancelAfter(TimeSpan.FromSeconds(timeLimitInSeconds));

            try
            {
                while (!cts.IsCancellationRequested)
                {
                    AIprobe.Models.Environment initialState = CloneEnvironment(environmentConfig);
                    //AIprobe.Models.Environment finalState = CloneEnvironment(environmentConfig);

                    // gentrating new initial state
                    MutateAgentProperties(initialState);
                    //MutateObjectProperties((initialState));

                    AIprobe.Models.Environment finalState = CloneEnvironment(initialState);
                    MutateAgentProperties(finalState);
                    //MutateObjectProperties((finalState));
                    tasks.Add((initialState, finalState));
                }
            }
            catch (OperationCanceledException)
            {
            }
            finally
            {
                cts.Dispose();
            }

            Logger.LogInfo(
                $"Task generation completed. {tasks.Count} tasks were generated within {timeLimitInSeconds} seconds.");
            return tasks;
        }

        //
        //
        /// <summary>
        /// This method processes the mutable properties of agents within the environment.
        /// It selects random mutable attributes and modifies them accordingly.
        /// </summary>
        /// <param name="environmentConfig"></param>
        /// <returns></returns>
        private Environment MutateAgentProperties(Environment environmentConfig)
        {
            var mutableAttributes = ProcessAgentListForMutableAttributes(environmentConfig.Agents.AgentList);

            Dictionary<string, List<string>>
                selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);

            ModifyMutableAttributes(environmentConfig.Agents.AgentList, mutableAttributes);

            return environmentConfig;
        }

        //
        /// <summary>
        /// Processes a list of agents and identifies mutable attributes.
        /// </summary>
        /// <param name="agentList">The list of agents to process.</param>
        /// <returns>
        /// A dictionary where the key is the agent's ID , and the value is a list of mutable attribute names for that agent.
        /// </returns>
        private Dictionary<string, List<string>> ProcessAgentListForMutableAttributes(
            List<AIprobe.Models.Agent> agentList)
        {
            Dictionary<string, List<string>> agentMutableAttributes = new Dictionary<string, List<string>>();

            foreach (var agent in agentList)
            {
                List<string> mutableAttributeNames = new List<string>();

                // Process Position attributes
                foreach (var attr in agent.Attributes)
                {
                    if (attr.Mutable?.Value == true)
                    {
                        mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
                    }
                }


                // If there are mutable attributes, add them to the dictionary with the agent's ID
                if (mutableAttributeNames.Count > 0)
                {
                    agentMutableAttributes[agent.Id.ToString()] = mutableAttributeNames;
                }
            }

            return agentMutableAttributes; // Return the dictionary with agent ID and mutable attribute names
        }

        //
        /// <summary>
        /// Randomly selects a subset of values from each key's list in the provided dictionary. 
        /// </summary>
        /// <param name="attributesDictionary">
        /// A dictionary where the key is eithe agent id or object id  and the value  is a list of mutable attribute names associated with that entity.
        /// </param>
        /// <returns>
        /// A dictionary where the key is eithe agent id or object id  and the value is a random list of mutable attribute names associated with that entity.
        /// </returns>
        private Dictionary<string, List<string>> RandomlySelectValuesFromDictionary(
            Dictionary<string, List<string>> attributesDictionary)
        {
            Random random = new Random();
            Dictionary<string, List<string>> selectedValuesDictionary = new Dictionary<string, List<string>>();

            // Iterate over each key in the dictionary
            foreach (var entry in attributesDictionary)
            {
                string key = entry.Key; // The key (Agent or Object ID)
                List<string> values = entry.Value; // The list of mutable attribute names for this key

                if (values.Count == 0)
                {
                    // If there are no values for this key, skip
                    continue;
                }

                // Randomly decide how many values to select for this key (between 1 and the total number of values)
                int numberToSelect = random.Next(1, values.Count);

                List<string> selectedValues = new List<string>();

                // Randomly select unique values
                while (selectedValues.Count < numberToSelect)
                {
                    int index = random.Next(0, values.Count); // Random index
                    string selectedValue = values[index];

                    if (!selectedValues.Contains(selectedValue)) // Ensure no duplicates
                    {
                        selectedValues.Add(selectedValue);
                    }
                }

                // Add the selected values to the result dictionary
                selectedValuesDictionary[key] = selectedValues;
            }

            return selectedValuesDictionary;
        }

        //
        //
        /// <summary>
        /// Modifies the mutable attributes for a list of agents based on the provided dictionary of mutable attributes.
        /// </summary>
        /// <param name="agentList">The list of agents to process for mutable attributes.</param>
        /// <param name="mutableAttributes">
        /// A dictionary where the key is the agent's id, and the value is a list of mutable attribute names that should be modified for that agent.
        /// </param>
        private void ModifyMutableAttributes(List<AIprobe.Models.Agent> agentList,
            Dictionary<string, List<string>> mutableAttributes)
        {
            foreach (var agent in agentList)
            {
                if (mutableAttributes.ContainsKey(agent.Id.ToString()))
                {
                    // Get the mutable attribute names for this agent
                    List<string> attributesToMutate = mutableAttributes[agent.Id.ToString()];

                    // Modify Position attributes and store the selected values
                    ModifyEntityAttributes(agent.Attributes, attributesToMutate);

                    // Modify Direction attributes and store the selected values
                    //ModifyEntityAttributes(agent.Direction.Attributes, attributesToMutate);
                }
            }
        }

        //
        //
        // /// <summary>
        // /// This method processes the mutable properties of objects within the environment.
        // /// It selects random mutable attributes and modifies them accordingly.
        // /// </summary>
        // /// <param name="environmentConfig"></param>
        // /// <returns></returns>
        internal Environment MutateObjectProperties(Environment environmentConfig)
        {
            var mutableAttributes = ProcessObjectListForMutableAttributes(environmentConfig.Objects.ObjectList);

            // Randomly select indices from mutable attributes
            //Dictionary<string, List<string>> selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);

            //ModifyMutableObjects(environmentConfig, mutableAttributes);
            //ModifyMutableObjectsD(environmentConfig, mutableAttributes);

            ModifyMutableObjectsNotRandom(environmentConfig, mutableAttributes);
            //ModifyMutableObjectsUsingOrthogonalMatrix(environmentConfig, mutableAttributes);

            return environmentConfig;
        }

        //
        //
        /// <summary>
        /// process object list and gather mutable attribute names
        /// </summary>
        /// <param name="objectList"></param>
        /// <returns></returns>
        private Dictionary<string, List<string>> ProcessObjectListForMutableAttributes(
            List<AIprobe.Models.Object> objectList)
        {
            Dictionary<string, List<string>> objectMutableAttributes = new Dictionary<string, List<string>>();

            foreach (var obj in objectList)
            {
                List<string> mutableAttributeNames = new List<string>();


                // Process Object attributes
                foreach (var attr in obj.Attributes)
                {
                    if (attr.Mutable?.Value == true)
                    {
                        mutableAttributeNames.Add(attr.Name.Value); // Add the name of the mutable attribute
                    }
                }


                // If there are mutable attributes, add them to the dictionary with the object's ID
                if (mutableAttributeNames.Count > 0)
                {
                    objectMutableAttributes[obj.Id.ToString()] = mutableAttributeNames;
                }
            }

            return objectMutableAttributes; // Return the dictionary with object ID and mutable attribute names
        }

        //
        //
        /// <summary>
        /// Modify mutable attributes for Objects,based on the dictionary of mutable attributes
        /// </summary>
        /// <param name="objectList"></param>
        /// <param name="mutableAttributes"></param>
        private void ModifyMutableObjects(Environment environmentConfig,
            Dictionary<string, List<string>> mutableAttributes)
        {
            foreach (var obj in environmentConfig.Objects.ObjectList)
            {
                string objectId = obj.Id.ToString();

                // Check if the current object has an entry in mutableAttributes
                if (mutableAttributes.ContainsKey(objectId))
                {
                    List<string> attributesToMutate = mutableAttributes[objectId];

                    // Deep copy the attributes to avoid shared references
                    List<Attribute> deepCopiedAttributes = obj.Attributes
                        .Select(attribute => CloneAttribute(attribute))
                        .ToList();
                    obj.Attributes = deepCopiedAttributes;

                    foreach (var attribute in obj.Attributes)
                    {
                        // Ensure the attribute matches the list for the current object
                        if (attributesToMutate.Contains(attribute.Name.Value))
                        {
                            // Generate a new value for the current attribute
                            var newValue = ChangeAttributeValue(attribute);

                            // Log original and new values for debugging

                            // Assign the mutated value to the attribute
                            attribute.Value.Content = newValue.ToString();
                        }
                    }
                }
            }
        }
        
        
        
        
        // private void ModifyMutableObjectsNotRandom(Environment environmentConfig, Dictionary<string, List<string>> mutableAttributes)
        // {
        //     foreach (var obj in environmentConfig.Objects.ObjectList)
        //     {
        //         string objectId = obj.Id.ToString();
        //
        //         // Check if the current object has an entry in mutableAttributes
        //         if (mutableAttributes.ContainsKey(objectId))
        //         {
        //             List<string> attributesToMutate = mutableAttributes[objectId];
        //
        //             // Deep copy the attributes to avoid shared references
        //             List<Attribute> deepCopiedAttributes = obj.Attributes
        //                 .Select(attribute => CloneAttribute(attribute))
        //                 .ToList();
        //             obj.Attributes = deepCopiedAttributes;
        //
        //             foreach (var attribute in obj.Attributes)
        //             {
        //                 // Ensure the attribute matches the list for the current object
        //                 if (attributesToMutate.Contains(attribute.Name.Value))
        //                 {
        //                     // Generate a new value for the current attribute
        //                     var newValue = ChangeAttributeValue(attribute);
        //
        //                     // Log original and new values for debugging
        //           
        //                     // Assign the mutated value to the attribute
        //                     attribute.Value.Content = newValue.ToString();
        //
        //                 }
        //             }
        //         }
        //     }
        //
        // }


        private void ModifyMutableObjectsNotRandom(Environment environmentConfig,
            Dictionary<string, List<string>> mutableAttributes)
        {
            // Dictionary to track unique attribute value combinations
            var attributeValueMap = new Dictionary<string, string>(); // Key: Combination, Value: Object ID

            // Generate all possible combinations for attributes
            var allCombinations = GenerateAllCombinations(environmentConfig, mutableAttributes);
            
            var random = new Random(Aiprobe.seed);
            allCombinations = allCombinations.OrderBy(_ => random.Next()).ToList();

            
            int combinationIndex = 0;

            foreach (var obj in environmentConfig.Objects.ObjectList)
            {
                string objectId = obj.Id.ToString();

                // Check if the current object has an entry in mutableAttributes
                if (mutableAttributes.ContainsKey(objectId))
                {
                    List<string> attributesToMutate = mutableAttributes[objectId];

                    // Deep copy the attributes to avoid shared references
                    List<Attribute> deepCopiedAttributes = obj.Attributes
                        .Select(attribute => CloneAttribute(attribute))
                        .ToList();
                    obj.Attributes = deepCopiedAttributes;

                    // Get the next available combination for this object
                    if (combinationIndex >= allCombinations.Count)
                    {
                        throw new InvalidOperationException(
                            "Not enough unique combinations available for all objects.");
                    }

                    List<string> selectedCombination = allCombinations[combinationIndex];
                    combinationIndex++;

                    // Assign the combination values to the object's attributes
                    for (int i = 0; i < attributesToMutate.Count; i++)
                    {
                        string attributeName = attributesToMutate[i];
                        string attributeValue = selectedCombination[i];

                        // Find the attribute and update its value
                        var attribute = obj.Attributes.FirstOrDefault(attr => attr.Name.Value == attributeName);
                        if (attribute != null)
                        {
                            attribute.Value.Content = attributeValue;
                        }
                    }
                }
            }
        }


        // Generate all possible combinations for mutable attributes
        private List<List<string>> GenerateAllCombinations(Environment environmentConfig,
            Dictionary<string, List<string>> mutableAttributes)
        {
            var combinations = new List<List<string>>();

            foreach (var obj in environmentConfig.Objects.ObjectList)
            {
                string objectId = obj.Id.ToString();

                if (mutableAttributes.ContainsKey(objectId))
                {
                    var attributeRanges = mutableAttributes[objectId]
                        .Select(attributeName =>
                        {
                            var attribute = obj.Attributes.First(attr => attr.Name.Value == attributeName);
                            int min = int.Parse(attribute.Constraint.Min);
                            int max = int.Parse(attribute.Constraint.Max);

                            // Generate range of values
                            return Enumerable.Range(min, max - min + 1).Select(v => v.ToString()).ToList();
                        })
                        .ToList();

                    // Cartesian product for all attribute ranges
                    combinations.AddRange(CartesianProduct(attributeRanges));
                }
            }

            return combinations;
        }


        // Helper to compute the Cartesian product of multiple lists
        private List<List<string>> CartesianProduct(List<List<string>> lists)
        {
            IEnumerable<IEnumerable<string>> result = new[] { Enumerable.Empty<string>() };

            foreach (var list in lists)
            {
                result = result.SelectMany(r => list, (r, item) => r.Append(item));
            }

            return result.Select(r => r.ToList()).ToList();
        }


// Helper method to check for conflicts in the attribute combination
        private bool IsCombinationConflict(List<string> currentCombination, string newValue,
            Dictionary<string, string> attributeValueMap)
        {
            var tempCombination = new List<string>(currentCombination) { newValue };
            string tempKey = string.Join(",", tempCombination);
            return attributeValueMap.ContainsKey(tempKey);
        }


        private Attribute CloneAttribute(Attribute original)
        {
            return new Attribute
            {
                Name = original.Name,
                Value = new Value { Content = original.Value.Content },
                DataType = original.DataType,
                Constraint = new Constraint
                {
                    Min = original.Constraint.Min,
                    Max = original.Constraint.Max
                }
            };
        }

        //
        /// <summary>
        /// to modify entity attributes (used by both Agent and Object) and store selected values
        /// </summary>
        /// <param name="attributes"></param>
        /// <param name="attributesToMutate"></param>
        private void ModifyEntityAttributes(List<Attribute> attributes, List<string> attributesToMutate)
        {
            foreach (var attr in attributes)
            {
                // Check if this attribute's name is in the list of names to mutate
                if (attributesToMutate.Contains(attr.Name.Value))
                {
                    // Apply changes to the attribute
                    var newValue = ChangeAttributeValue(attr); // Example of modifying the attribute value

                    // Assign the mutated value back to the attribute
                    attr.Value.Content = newValue.ToString();
                }
            }
        }


        /// <summary>
        /// Randomly change the value of the attribute based on the data type
        /// </summary>
        /// <param name="attr">Attributes of the agent or object</param>
        /// <returns>Modified value of the attribute</returns>
        private object ChangeAttributeValue(AIprobe.Models.Attribute attr)
        {
            // Ensure constraints are valid
            if (attr.Constraint.Min == attr.Constraint.Max)
            {
                return attr.Constraint.Min; // Return Min as fallback
            }

            // Change the value based on the data type
            if (attr.DataType.Value == "int")
            {
                int newValue = random.Next(Convert.ToInt32(attr.Constraint.Min), Convert.ToInt32(attr.Constraint.Max));

                return newValue;
            }
            else if (attr.DataType.Value == "float")
            {
                float newValue =
                    (float)(random.NextDouble() *
                            (Convert.ToSingle(attr.Constraint.Max) - Convert.ToSingle(attr.Constraint.Min)) +
                            Convert.ToSingle(attr.Constraint.Min));

                return newValue;
            }
            else if (attr.DataType.Value == "bool")
            {
                bool newValue = random.Next(0, 2) == 0;
                Console.WriteLine($"Generated bool value for {attr.Name.Value}: {newValue}");
                return newValue;
            }

            // Default: return the original value if no change is needed
            Console.WriteLine($"No change for {attr.Name.Value}. Returning original value: {attr.Value.Content}");
            return attr.Value.Content;
        }

        public static List<Environment> TaskGenerator(Environment baseEnv, double envcount, int? seed = null)
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

                    dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                        DataType: dataType);
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

                        dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                            DataType: dataType);
                    }

                    dataTypes.Add(dataType);
                }
            }

            try
            {
                // foreach (var obj in baseEnv.Objects.ObjectList)
                // {
                //     foreach (var attr in obj.Attributes.Where(attr => attr.Mutable.Value))
                //     {
                //         string key = $"Object_{obj.Id}_{attr.Name.Value}";
                //         string minExpr = attr.Constraint.Min ?? "0";
                //         string maxExpr = attr.Constraint.Max ?? "0";
                //         string dataType = attr.DataType.Value;
                //
                //         if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                //         {
                //             independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
                //         }
                //         else
                //         {
                //             string strippedMinExpr = StripBraces(minExpr);
                //             string strippedMaxExpr = StripBraces(maxExpr);
                //
                //             dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr, DataType: dataType);
                //         }
                //
                //         dataTypes.Add(dataType);
                //     }
                // }
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
                throw;
            }
            // Process object attributes
            // foreach (var obj in baseEnv.Objects.ObjectList)
            // {
            //     foreach (var attr in obj.Attributes.Where(attr => attr.Mutable.Value))
            //     {
            //         string key = $"Object_{obj.Id}_{attr.Name.Value}";
            //         string minExpr = attr.Constraint.Min ?? "0";
            //         string maxExpr = attr.Constraint.Max ?? "0";
            //         string dataType = attr.DataType.Value;
            //
            //         if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
            //         {
            //             independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
            //         }
            //         else
            //         {
            //             string strippedMinExpr = StripBraces(minExpr);
            //             string strippedMaxExpr = StripBraces(maxExpr);
            //
            //             dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr, DataType: dataType);
            //         }
            //
            //         dataTypes.Add(dataType);
            //     }
            // }

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


        // Testing


        public List<(Environment, Environment)> GenerateTasksUsingOrthogonalSampling(Environment environmentConfig,
            int nSamples, int? seed = null, string outputFilePath = null)
        {
            // Resolve mutable constraints
            var (independentRanges, _, _) = ResolveMutableConstraints(environmentConfig);


            // Prepare ranges for sampling
            Dictionary<string, (double Min, double Max)> ranges = independentRanges.ToDictionary(
                kvp => kvp.Key,
                kvp => (kvp.Value.Min, kvp.Value.Max)
            );

            nSamples = independentRanges.Count * 10;

            // Generate orthogonal samples
            List<int[]> orthogonalSamples = GenerateOrthogonalSamples(nSamples, ranges.Count, ranges, seed);


            orthogonalSamples = RemoveDuplicateSamples(orthogonalSamples);
            
            //Save the generated points to a CSV file (optional)
            if (!string.IsNullOrEmpty(outputFilePath))
            {
                SaveSamplesToCsv(orthogonalSamples, ranges.Keys.ToList(), "generated_orthogoal_samples.csv");
            }


            List<int[]> randomSamples = GenerateRandomSamples(nSamples, ranges.Count, ranges, seed);

            // Save the generated points to a CSV file (optional)
            if (!string.IsNullOrEmpty(outputFilePath))
            {
                SaveSamplesToCsv(randomSamples, ranges.Keys.ToList(), "generated_Random_samples.csv");
            }


            List<int[]> lHSsampole = LhsSampler.GenerateLHSSamples(nSamples, ranges, seed);

            if (!string.IsNullOrEmpty(outputFilePath))
            {
                SaveSamplesToCsv(randomSamples, ranges.Keys.ToList(), "generated_LHS_samples.csv");
            }


            // Generate tasks
            List<(Environment, Environment)> tasks = new List<(Environment, Environment)>();

            foreach (var sample in orthogonalSamples)
            {
                Environment initialState = CloneEnvironment(environmentConfig);
                Environment finalState = CloneEnvironment(environmentConfig);

                // Apply sampled values to the initial state
                int index = 0;
                foreach (var key in ranges.Keys)
                {
                    ApplySampleToEnvironment(initialState, key, sample[index]);
                    index++;
                }

                // Mutate to create the final state
                MutateAgentProperties(finalState);
                //MutateObjectProperties(finalState);

                tasks.Add((initialState, finalState));
            }

            Logger.LogInfo($"Orthogonal sampling completed. Generated {tasks.Count} tasks.");
            return tasks;
        }
        
        private List<int[]> RemoveDuplicateSamples(List<int[]> orthogonalSamples)
        {
            // Use a HashSet with a custom comparer to ensure uniqueness based on array content
            var uniqueSamples = new HashSet<int[]>(new ArrayComparer());

            foreach (var sample in orthogonalSamples)
            {
                uniqueSamples.Add(sample); // HashSet will automatically handle duplicates
            }

            // Convert back to a List<int[]> and return
            return uniqueSamples.ToList();
        }
        
        // Custom comparer for int[] to compare array content
        private class ArrayComparer : IEqualityComparer<int[]>
        {
            public bool Equals(int[] x, int[] y)
            {
                if (x == null || y == null) return false;
                if (x.Length != y.Length) return false;

                // Compare arrays element by element
                for (int i = 0; i < x.Length; i++)
                {
                    if (x[i] != y[i])
                    {
                        return false;
                    }
                }

                return true;
            }

            public int GetHashCode(int[] obj)
            {
                if (obj == null) return 0;

                // Combine hash codes of all elements in the array
                unchecked
                {
                    int hash = 17;
                    foreach (int value in obj)
                    {
                        hash = hash * 31 + value.GetHashCode();
                    }
                    return hash;
                }
            }
        }

        private void ApplySampleToEnvironment(Environment env, string attributeName, double sampledValue)
        {
            // foreach (var attr in env.Attributes)
            // {
            //     if (attr.Name.Value == attributeName && attr.Mutable?.Value == true)
            //     {
            //         attr.Value.Content = Convert.ToString(sampledValue);
            //     }
            // }

            foreach (var agent in env.Agents.AgentList)
            {
                string[] parts = attributeName.Split('_');


                string lastWord = parts[^1]; // ^1 is the index-from-end operator

                foreach (var attr in agent.Attributes)
                {
                    if (attr.Name.Value == lastWord && attr.Mutable?.Value == true)
                    {
                        attr.Value.Content = Convert.ToString(sampledValue);
                    }
                }
            }

            // foreach (var obj in env.Objects.ObjectList)
            // {
            //     foreach (var attr in obj.Attributes)
            //     {
            //         if (attr.Name.Value == attributeName && attr.Mutable?.Value == true)
            //         {
            //             attr.Value.Content = Convert.ToString(sampledValue);
            //         }
            //     }
            // }
        }

        private List<int[]> GenerateOrthogonalSamples(int nSamples, int nDimensions,
            Dictionary<string, (double Min, double Max)> ranges, int? seed = null)
        {
            Random random = seed.HasValue ? new Random(seed.Value) : new Random();

            // Step 1: Create an empty matrix for samples
            List<int[]> samples = new List<int[]>();

            // Step 2: Divide each dimension into equal intervals
            var intervals = new Dictionary<int, List<int>>();
            int dimensionIndex = 0;
            foreach (var range in ranges)
            {
                string key = range.Key;
                double min = range.Value.Min;
                double max = range.Value.Max;

                // Generate stratified intervals for this dimension as integers
                List<int> stratifiedIntervals = Enumerable.Range(0, nSamples)
                    .Select(i => (int)Math.Round(min + (i + random.NextDouble()) * (max - min) / nSamples))
                    .OrderBy(_ => random.Next()) // Shuffle intervals
                    .ToList();

                intervals[dimensionIndex] = stratifiedIntervals;
                dimensionIndex++;
            }

            // Step 3: Create the orthogonal matrix
            for (int i = 0; i < nSamples; i++)
            {
                int[] sample = new int[nDimensions];

                for (int j = 0; j < nDimensions; j++)
                {
                    // Assign intervals in an orthogonal manner
                    sample[j] = intervals[j][i];
                }

                samples.Add(sample);
            }

            // Shuffle rows to introduce randomness
            samples = samples.OrderBy(_ => random.Next()).ToList();

            return samples;
        }

        private void SaveSamplesToCsv(List<int[]> samples, List<string> headers, string filePath)
        {
            using (var writer = new System.IO.StreamWriter(filePath))
            {
                // Write the headers
                writer.WriteLine(string.Join(",", headers));

                // Write each sample as a row
                foreach (var sample in samples)
                {
                    writer.WriteLine(string.Join(",",
                        sample.Select(value => value.ToString(System.Globalization.CultureInfo.InvariantCulture))));
                }
            }

            Logger.LogInfo($"Generated samples saved to: {filePath}");
        }


        private List<int[]> GenerateRandomSamples(int nSamples, int nDimensions,
            Dictionary<string, (double Min, double Max)> ranges, int? seed = null)
        {
            Random random = seed.HasValue ? new Random(seed.Value) : new Random();

            // Create a list to store random samples
            List<int[]> samples = new List<int[]>();

            for (int i = 0; i < nSamples; i++)
            {
                int[] sample = new int[nDimensions];
                int dimensionIndex = 0;

                // Generate random values for each dimension within the specified range
                foreach (var range in ranges)
                {
                    double min = range.Value.Min;
                    double max = range.Value.Max;

                    // Generate a random integer value within the range
                    sample[dimensionIndex] = random.Next((int)Math.Floor(min), (int)Math.Ceiling(max) + 1);
                    dimensionIndex++;
                }

                samples.Add(sample);
            }

            return samples;
        }


        private List<int[]> GenerateLHSSamples(int nSamples, int nDimensions,
            Dictionary<string, (double Min, double Max)> ranges, int? seed = null)
        {
            Random random = seed.HasValue ? new Random(seed.Value) : new Random();

            // Create a list to store LHS samples
            List<int[]> samples = new List<int[]>();

            // Step 1: Divide each dimension into equal intervals
            var intervals = new Dictionary<int, List<int>>();
            int dimensionIndex = 0;

            foreach (var range in ranges)
            {
                double min = range.Value.Min;
                double max = range.Value.Max;

                // Create stratified intervals as integers
                List<int> stratifiedIntervals = Enumerable.Range(0, nSamples)
                    .Select(i => (int)Math.Round(min + i * (max - min) / nSamples))
                    .ToList();

                // Shuffle intervals to ensure randomness
                for (int i = stratifiedIntervals.Count - 1; i > 0; i--)
                {
                    int j = random.Next(i + 1);
                    (stratifiedIntervals[i], stratifiedIntervals[j]) = (stratifiedIntervals[j], stratifiedIntervals[i]);
                }

                intervals[dimensionIndex] = stratifiedIntervals;
                dimensionIndex++;
            }

            // Step 2: Generate the LHS sample matrix
            for (int i = 0; i < nSamples; i++)
            {
                int[] sample = new int[nDimensions];

                for (int j = 0; j < nDimensions; j++)
                {
                    // Assign one interval per dimension for this sample
                    sample[j] = intervals[j][i];
                }

                samples.Add(sample);
            }

            return samples;
        }


        private void ModifyMutableObjectsUsingOrthogonalMatrix(Environment environmentConfig,
            Dictionary<string, List<string>> mutableAttributes)
        {
            // Dictionary to track unique attribute value combinations
            var attributeValueMap = new Dictionary<string, string>(); // Key: Combination, Value: Object ID

            // Generate all possible combinations for attributes
            var allCombinations = GenerateAllCombinations(environmentConfig, mutableAttributes);

            if (allCombinations.Count == 0)
            {
                return;
            }

            // Generate an orthogonal matrix
            var orthogonalSamples = GenerateOrthogonalMatrix(allCombinations.Count, allCombinations[0].Count);

            // Scale orthogonal samples to match allCombinations
            var selectedCombinations = MapOrthogonalSamplesToCombinations(allCombinations, orthogonalSamples);

            // Assign combinations to objects
            int combinationIndex = 0;
            foreach (var obj in environmentConfig.Objects.ObjectList)
            {
                string objectId = obj.Id.ToString();

                // Check if the current object has an entry in mutableAttributes
                if (mutableAttributes.ContainsKey(objectId) && combinationIndex < selectedCombinations.Count)
                {
                    List<string> attributesToMutate = mutableAttributes[objectId];

                    // Deep copy the attributes to avoid shared references
                    List<Attribute> deepCopiedAttributes = obj.Attributes
                        .Select(attribute => CloneAttribute(attribute))
                        .ToList();
                    obj.Attributes = deepCopiedAttributes;

                    // Get the selected combination for this object
                    var selectedCombination = selectedCombinations[combinationIndex];
                    combinationIndex++;

                    int index = 0;
                    foreach (var attribute in obj.Attributes)
                    {
                        // Ensure the attribute matches the list for the current object
                        if (attributesToMutate.Contains(attribute.Name.Value))
                        {
                            // Assign the value from the selected combination
                            attribute.Value.Content = selectedCombination[index];
                            index++;
                        }
                    }
                }
            }
        }

// Generate an orthogonal matrix
        private List<List<double>> GenerateOrthogonalMatrix(int numRows, int numCols)
        {
            var random = new Random(Aiprobe.seed);
            var orthogonalMatrix = new List<List<double>>();

            for (int i = 0; i < numRows; i++)
            {
                var row = new List<double>();
                for (int j = 0; j < numCols; j++)
                {
                    // Generate values between 0 and 1
                    row.Add(random.NextDouble());
                }

                orthogonalMatrix.Add(row);
            }

            // Ensure orthogonality by normalizing rows
            orthogonalMatrix = NormalizeOrthogonalMatrix(orthogonalMatrix);
            return orthogonalMatrix;
        }

// Normalize the orthogonal matrix
        private List<List<double>> NormalizeOrthogonalMatrix(List<List<double>> matrix)
        {
            var normalizedMatrix = new List<List<double>>();

            foreach (var row in matrix)
            {
                double norm = Math.Sqrt(row.Sum(value => value * value));
                normalizedMatrix.Add(row.Select(value => value / norm).ToList());
            }

            return normalizedMatrix;
        }

// Map orthogonal samples to combinations
        private List<List<string>> MapOrthogonalSamplesToCombinations(List<List<string>> allCombinations,
            List<List<double>> orthogonalSamples)
        {
            var mappedCombinations = new List<List<string>>();

            for (int i = 0; i < orthogonalSamples.Count; i++)
            {
                var combination = new List<string>();

                for (int j = 0; j < orthogonalSamples[i].Count; j++)
                {
                    // Map normalized value to combination index
                    int index = (int)(orthogonalSamples[i][j] * allCombinations.Count);
                    index = Math.Min(index, allCombinations.Count - 1); // Ensure within bounds
                    combination.Add(allCombinations[index][j]);
                }

                mappedCombinations.Add(combination);
            }

            return mappedCombinations;
        }

// Generate all possible combinations for mutable attributes
    }
}