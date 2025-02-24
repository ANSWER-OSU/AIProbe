using System;
using System.Collections.Generic;
using System.Data;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using AIprobe.Models;
using Constraint = AIprobe.Models.Constraint;
using System.Collections.Concurrent;

namespace AIprobe
{
    using Attribute = AIprobe.Models.Attribute;
    using Environment = AIprobe.Models.Environment;
    using Object = AIprobe.Models.Object;

    public class EnvConfigGenerator
    {
        public static ConcurrentQueue<Environment> GenerateEnvConfigsQueue(Environment baseEnv, int seed = 0)
        {
            // Step 1: Resolve constraints into independent ranges and dependencies
            var (independentRanges, dependentConstraints, dataTypes) = ResolveConstraints(baseEnv);

          
            double samples = Math.Pow(Aiprobe.bin,
                independentRanges.Count + dependentConstraints.Count);
            Aiprobe.LogAndDisplay($"Total {samples} environment samples will be generated");
            //int nSamples = (independentRanges.Count + dependentConstraints.Count) * Aiprobe.enviromentSampleConstant;
            Aiprobe.LogAndDisplay($"Total {samples} environment samples will be generated");

            var improvedLHS =
                LhsSampler.PerformLhsWithDependenciesImproved(independentRanges, dependentConstraints, samples, seed);


            if (!Directory.Exists(Aiprobe.resultFolder))
            {
                Directory.CreateDirectory(Aiprobe.resultFolder);
            }


            SaveToCsv(improvedLHS, $"{Aiprobe.resultFolder}/improvedLHS_values_seed{seed}.csv");

            ConcurrentQueue<Environment> sampledEnvironments = new ConcurrentQueue<Environment>();
            Aiprobe.LogAndDisplay($"Total no of environment generated: {improvedLHS.Count}");
            int sampleCount = 0;

            if (dependentConstraints.Count != 0)
            {
                foreach (var sample in improvedLHS)
                {
                    var newEnv = CloneEnvironment(baseEnv); // Clone the base environment
                    ApplySamplesToEnvironment(newEnv, sample, dataTypes);

                    // Step 5: Adjust objects based on global attributes
                    AdjustObjectsGlobally(newEnv);

                    Environment modifiedEnv = MutateObjectProperties(newEnv,seed);


                    Aiprobe.LogAndDisplay(
                        $"Saved the generated sample env no: {sampledEnvironments.Count() + 1} in memory");

                    // Enqueue the environment
                    sampledEnvironments.Enqueue(modifiedEnv);
                }
            }
            else
            {
                foreach (var sample in improvedLHS)
                {
                    var newEnv = CloneEnvironment(baseEnv); // Clone the base environment
                    ApplySamplesToEnvironment(newEnv, sample, dataTypes);
                    sampledEnvironments.Enqueue(newEnv);
                }
            }


            Aiprobe.LogAndDisplay($"Total no of environment generated and saved: {sampledEnvironments.Count}");
            return sampledEnvironments;
        }

        
           public static (Dictionary<string, (double Min, double Max, string DataType,int RoundOff)> independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType,int RoundOff)> dependentConstraints,
            List<string> dataTypes)
            ResolveConstraints(Environment baseEnv)
        {
            var independentRanges = new Dictionary<string, (double Min, double Max, string DataType,int RoundOff)>();
            var dependentConstraints = new Dictionary<string, (string MinExpr, string MaxExpr, string DataType,int RoundOff)>();
            var dataTypes = new List<string>();

            foreach (var attr in baseEnv.Attributes)
            {
                string attrName = attr.Name.Value;
                string minExpr = attr.Constraint.Min ?? "0";
                string maxExpr = attr.Constraint.Max ?? "0";
                string dataType = attr.DataType.Value;
                string roundOff = string.IsNullOrEmpty(attr.Constraint.RoundOff) ? "0" : attr.Constraint.RoundOff;

                if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                {
                    // Independent constraint
                    independentRanges[attrName] = (double.Parse(minExpr), double.Parse(maxExpr), dataType,int.Parse(roundOff));
                }
                else
                {
                    // Dependent constraint: Strip enclosing braces and store the raw expressions
                    string strippedMinExpr = StripBraces(minExpr);
                    string strippedMaxExpr = StripBraces(maxExpr);

                    dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                        DataType: dataType,int.Parse(roundOff));
                }

                dataTypes.Add(dataType);
            }
            
            
            
            
            foreach (var attr in baseEnv.Objects.ObjectList)
            {
                foreach (var VARIABLE in attr.Attributes)
                {
                    string attrName = VARIABLE.Name.Value;
                    string minExpr = VARIABLE.Constraint.Min ?? "0";
                    string maxExpr = VARIABLE.Constraint.Max ?? "0";
                    string dataType = VARIABLE.DataType.Value;
                    string roundOff = string.IsNullOrEmpty(VARIABLE.Constraint.RoundOff) ? "0" : VARIABLE.Constraint.RoundOff;

                    if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                    {
                        // Independent constraint
                        independentRanges[attrName] = (double.Parse(minExpr), double.Parse(maxExpr), dataType,int.Parse(roundOff));
                    }
                    else
                    {
                        // Dependent constraint: Strip enclosing braces and store the raw expressions
                        string strippedMinExpr = StripBraces(minExpr);
                        string strippedMaxExpr = StripBraces(maxExpr);

                        dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                            DataType: dataType,int.Parse(roundOff));
                    }

                    dataTypes.Add(dataType);
                }

                }
               
            
            
            

            return (independentRanges, dependentConstraints, dataTypes);
        }

        

        internal static Environment MutateObjectProperties(Environment environmentConfig,int seed)
        {
            var mutableAttributes = ProcessObjectListForMutableAttributes(environmentConfig.Objects.ObjectList);

            // Randomly select indices from mutable attributes
            //Dictionary<string, List<string>> selectedAttributess = RandomlySelectValuesFromDictionary(mutableAttributes);

            //ModifyMutableObjects(environmentConfig, mutableAttributes);
            //ModifyMutableObjectsD(environmentConfig, mutableAttributes);

            ModifyMutableObjectsNotRandom(environmentConfig, mutableAttributes,seed);
            //ModifyMutableObjectsUsingOrthogonalMatrix(environmentConfig, mutableAttributes);

            return environmentConfig;
        }
        
        
         private static void ModifyMutableObjectsNotRandom(Environment environmentConfig,
            Dictionary<string, List<string>> mutableAttributes,int seed)
        {
            // Dictionary to track unique attribute value combinations
            var attributeValueMap = new Dictionary<string, string>(); // Key: Combination, Value: Object ID

            // Generate all possible combinations for attributes
            var allCombinations = GenerateAllCombinations(environmentConfig, mutableAttributes);
            
            var random = new Random(seed);
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
        private static List<List<string>> GenerateAllCombinations(Environment environmentConfig,
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
        private static List<List<string>> CartesianProduct(List<List<string>> lists)
        {
            IEnumerable<IEnumerable<string>> result = new[] { Enumerable.Empty<string>() };

            foreach (var list in lists)
            {
                result = result.SelectMany(r => list, (r, item) => r.Append(item));
            }

            return result.Select(r => r.ToList()).ToList();
        }


        private static Attribute CloneAttribute(Attribute original)
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
        //
        /// <summary>
        /// process object list and gather mutable attribute names
        /// </summary>
        /// <param name="objectList"></param>
        /// <returns></returns>
        private static Dictionary<string, List<string>> ProcessObjectListForMutableAttributes(
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


        /// <summary>
        /// Adjusts objects and attributes dynamically based on global attributes.
        /// </summary>
        /// <param name="environment">The environment to adjust.</param>
        private static void AdjustObjectsGlobally(Environment environment)
        {
            // Retrieve all global attributes
            var globalAttributes = environment.Attributes;


            foreach (var agent in environment.Agents.AgentList)
            {
                foreach (var attribute in agent.Attributes)
                {
                    // Check if the attribute depends on a global attribute
                    foreach (var globalAttribute in globalAttributes)
                    {
                        var x = attribute.Constraint.Max;
                        var y = globalAttribute.Name.Value;
                        if (ContainsGlobalAttribute(attribute.Constraint.Max, globalAttribute.Name.Value) ||
                            ContainsGlobalAttribute(attribute.Constraint.Min, globalAttribute.Name.Value))
                        {
                            // Dynamically replace global placeholders in constraints
                            attribute.Constraint.Min =
                                ReplaceGlobalPlaceholder(attribute.Constraint.Min, globalAttributes);
                            attribute.Constraint.Max =
                                ReplaceGlobalPlaceholder(attribute.Constraint.Max, globalAttributes);
                        }
                    }
                }
            }


            // Loop through all objects and adjust based on matching global attributes
            foreach (var obj in environment.Objects.ObjectList)
            {
                foreach (var attribute in obj.Attributes)
                {
                    // Check if the attribute depends on a global attribute
                    foreach (var globalAttribute in globalAttributes)
                    {
                        var x = attribute.Constraint.Max;
                        var y = globalAttribute.Name.Value;
                        if (ContainsGlobalAttribute(attribute.Constraint.Max, globalAttribute.Name.Value) ||
                            ContainsGlobalAttribute(attribute.Constraint.Min, globalAttribute.Name.Value))
                        {
                            // Dynamically replace global placeholders in constraints
                            attribute.Constraint.Min =
                                ReplaceGlobalPlaceholder(attribute.Constraint.Min, globalAttributes);
                            attribute.Constraint.Max =
                                ReplaceGlobalPlaceholder(attribute.Constraint.Max, globalAttributes);
                        }
                    }
                }
            }

            // Dynamically add or adjust objects based on global attributes (e.g., count objects like Lava)
            foreach (var globalAttribute in globalAttributes)
            {
                foreach (var obj in environment.Objects.ObjectList)
                {
                    // Check if the object's type matches the global attribute name
                    if (obj.Type == globalAttribute.Name.Value)
                    {
                        AdjustObjectCount(environment, globalAttribute);
                        break; // Break out of the inner loop once a match is found
                    }
                }
            }
        }


        public static bool ContainsGlobalAttribute(string expression, string attributeName)
        {
            // Create a regex pattern to match the attribute name within curly braces
            string pattern = $@"\{{.*?\b{Regex.Escape(attributeName)}\b.*?\}}";

            // Check if the expression matches the pattern
            return Regex.IsMatch(expression, pattern);
        }


        /// <summary>
        /// Replaces placeholders in constraints with actual global values.
        /// </summary>
        /// <param name="constraintValue">The constraint value (e.g., "{Grid - 1}").</param>
        /// <param name="globalAttributes">The list of global attributes.</param>
        /// <returns>The updated constraint value.</returns>
        private static string ReplaceGlobalPlaceholder(string constraintValue, IEnumerable<Attribute> globalAttributes)
        {
            foreach (var globalAttribute in globalAttributes)
            {
                if (ContainsGlobalAttribute(constraintValue, globalAttribute.Name.Value))
                {
                    var expression = constraintValue.Replace(globalAttribute.Name.Value, globalAttribute.Value.Content);
                    var x = StripBraces(expression);
                    var dataTable = new DataTable();
                    return Convert.ToString(dataTable.Compute(x, null));
                }


                if (constraintValue.Contains($"{{{globalAttribute.Name.Value}}}"))
                {
                    var globalValue = int.Parse(globalAttribute.Value.Content);
                    constraintValue = constraintValue.Replace($"{{{globalAttribute.Name}}}", globalValue.ToString());
                }
            }

            // Evaluate any mathematical expression (if applicable)
            return EvaluateExpression(constraintValue);
        }

        /// <summary>
        /// Adjusts the number of objects of a specific type based on a global attribute.
        /// </summary>
        /// <param name="environment">The environment to adjust.</param>
        /// <param name="globalAttribute">The global attribute controlling the object count.</param>
        private static void AdjustObjectCount(Environment environment, Attribute globalAttribute)
        {
            // Find objects of the same type as the global attribute's name
            var matchingObjects = environment.Objects.ObjectList.Where(o => o.Type == globalAttribute.Name.Value)
                .ToList();
            int requiredCount = int.Parse(globalAttribute.Value.Content);
            int currentCount = matchingObjects.Count;

            if (requiredCount > currentCount)
            {
                // Add new objects to meet the required count
                for (int i = 0; i < requiredCount - currentCount; i++)
                {
                    var newObject = CloneObject(matchingObjects.First());
                    newObject.Id = ((environment.Objects.ObjectList.Count) + 1);
                    environment.Objects.ObjectList.Add(newObject);
                }
            }
            else if (requiredCount < currentCount)
            {
                // Remove excess objects
                for (int i = 0; i < currentCount - requiredCount; i++)
                {
                    environment.Objects.ObjectList.Remove(matchingObjects[i]);
                }
            }
        }


        /// <summary>
        /// Creates a clone of an object.
        /// </summary>
        /// <param name="sourceObject">The object to clone.</param>
        /// <returns>The cloned object.</returns>
        private static Object CloneObject(Object sourceObject)
        {
            return new Object
            {
                Id = sourceObject.Id,
                Type = sourceObject.Type,
                Attributes = sourceObject.Attributes.Select(attr => new Attribute
                {
                    Name = attr.Name,
                    DataType = attr.DataType,
                    Value = attr.Value,
                    Mutable = attr.Mutable,
                    Constraint = new Constraint
                    {
                        Min = attr.Constraint.Min,
                        Max = attr.Constraint.Max,
                        OneOf = attr.Constraint.OneOf,
                        RoundOff = attr.Constraint.RoundOff
                    }
                }).ToList()
            };
        }

        /// <summary>
        /// Evaluates mathematical expressions (e.g., "Grid - 1") to get numeric values.
        /// </summary>
        /// <param name="expression">The mathematical expression as a string.</param>
        /// <returns>The evaluated result as a string.</returns>
        private static string EvaluateExpression(string expression)
        {
            // Use a simple expression parser or implement basic evaluation logic
            try
            {
                var result = new DataTable().Compute(expression, null);
                return result.ToString();
            }
            catch
            {
                return expression; // Return original if unable to evaluate
            }
        }

        
        private static string StripBraces(string expression)
        {
            if (expression.StartsWith("{") && expression.EndsWith("}"))
            {
                return expression.Substring(1, expression.Length - 2); // Remove the leading and trailing braces
            }

            return expression;
        }
        

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
                    Constraint = new Constraint
                    {
                        Min = attr.Constraint.Min,
                        Max = attr.Constraint.Max,
                        OneOf = attr.Constraint.OneOf,
                        RoundOff = attr.Constraint.RoundOff
                    },
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
                            Constraint = new Constraint
                            {
                                Min = attr.Constraint.Min,
                                Max = attr.Constraint.Max,
                                OneOf = attr.Constraint.OneOf,
                                RoundOff = attr.Constraint.RoundOff
                            },
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
                            Constraint = new Constraint
                            {
                                Min = attr.Constraint.Min,
                                Max = attr.Constraint.Max,
                                OneOf = attr.Constraint.OneOf,
                                RoundOff = attr.Constraint.RoundOff
                            },
                            Mutable = attr.Mutable
                        }).ToList()
                    })
                }
            };
        }


        private static void ApplySamplesToEnvironment(Environment env, Dictionary<string, double> sample,
            List<string> dataTypes)
        {
            int dataTypeIndex = 0;

            // Update global attributes
            foreach (var attr in env.Attributes)
            {
                if (sample.ContainsKey(attr.Name.Value))
                {
                    attr.Value.Content = Convert.ToString(sample[attr.Name.Value]);
                    attr.DataType.Value = dataTypes.ElementAtOrDefault(dataTypeIndex++) ?? attr.DataType.Value;
                }
            }

            // Update agent attributes
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

            // Update object attributes
            foreach (var obj in env.Objects.ObjectList)
            {
                foreach (var attr in obj.Attributes)
                {
                    string sampleKey = $"{attr.Name.Value}";
                    if (sample.ContainsKey(sampleKey))
                    {
                        attr.Value.Content = Convert.ToString(sample[sampleKey]);
                        attr.DataType.Value = dataTypes.ElementAtOrDefault(dataTypeIndex++) ?? attr.DataType.Value;
                    }
                }
            }
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