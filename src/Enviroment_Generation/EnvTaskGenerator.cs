using System.Data;
using System.Text.RegularExpressions;
using AIprobe.Models;
using Environment = AIprobe.Models.Environment;
using Attribute = AIprobe.Models.Attribute;
using Constraint = AIprobe.Models.Constraint;
using Object = AIprobe.Models.Object;

namespace AIprobe.TaskGenerator
{
    public class EnvTaskGenerator
    {
        public List<(Environment, Environment)> GenerateTask(Environment environmentConfig, int seed,
            string resultFolder)
        {
            var (independentRanges, dependentConstraints, dataTypes) = ResolveConstraints(environmentConfig);

            Aiprobe.LogAndDisplay($"Total {Aiprobe.bin} environment samples will be generated");

            var (initialSamples, finalSamples) =
                LhsSampler.GenerateLhsSamplesForTask(independentRanges, dependentConstraints, seed);

            if (!Directory.Exists(resultFolder))
            {
                Directory.CreateDirectory(resultFolder);
            }
            
            int sampleCount = 0;
            EnvTaskGenerator gen = new EnvTaskGenerator();
            List<(Environment, Environment)> tasks = new List<(Environment, Environment)>();

            for (int i = 0; i < initialSamples.Count; i++)
            {
                var initialEnv = CloneEnvironment(environmentConfig);
                var finalEnv = CloneEnvironment(environmentConfig);
                if (Aiprobe.isTimeStep)
                {
                    var initialSample = initialSamples[i];
                    initialEnv = CloneEnvironment(environmentConfig);
                    finalEnv = CloneEnvironment(environmentConfig);
                    ApplySamplesToEnvironment(initialEnv, initialSample, dataTypes, true);
                    AdjustObjectsGlobally(initialEnv, true);
                    ApplySamplesToEnvironment(finalEnv, initialSample, dataTypes, false);
                }
                else
                {
                    var initialSample = initialSamples[i];
                    var finalSample = finalSamples[i];

                    initialEnv = CloneEnvironment(environmentConfig);
                    // Clone the base environment
                    ApplySamplesToEnvironment(initialEnv, initialSample, dataTypes, false);
                    AdjustObjectsGlobally(initialEnv, true);

                    finalEnv = CloneEnvironment(initialEnv);
                    
                    ApplySamplesToEnvironment(finalEnv, finalSample, dataTypes, false);
                    AdjustObjectsGlobally(finalEnv);
                }

                // Modify the environment properties

                Aiprobe.LogAndDisplay($"Saved the generated sample env no: {tasks.Count + 1} in memory");

                // Store the initial and final state as a tuple
                tasks.Add((initialEnv, finalEnv));
            }

            return tasks;
        }


        public static (Dictionary<string, (double Min, double Max, string DataType, string oneoff, int RoundOff)>
            independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType, string oneoff, int RoundOff)>
            dependentConstraints,
            List<string> dataTypes)
            ResolveConstraints(Environment baseEnv)
        {
            var independentRanges =
                new Dictionary<string, (double Min, double Max, string DataType, string onoff, int RoundOff)>();
            var dependentConstraints =
                new Dictionary<string, (string MinExpr, string MaxExpr, string oneoff, string DataType, int RoundOff
                    )>();
            var dataTypes = new List<string>();


            foreach (var attr in baseEnv.Agents.AgentList)
            {
                foreach (var VARIABLE in attr.Attributes)
                {
                    string attrName = VARIABLE.Name.Value;
                    string minExpr = VARIABLE.Constraint.Min ?? "0";
                    string maxExpr = VARIABLE.Constraint.Max ?? "0";
                    string dataType = VARIABLE.DataType.Value;
                    string oneoff = VARIABLE.Constraint.Values;
                    string roundOff = string.IsNullOrEmpty(VARIABLE.Constraint.Choice)
                        ? "0"
                        : VARIABLE.Constraint.Choice;

                    if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                    {
                        // Independent constraint
                        independentRanges["Agent_" + attr.Id + "_" + attrName] = (double.Parse(minExpr),
                            double.Parse(maxExpr), dataType, oneoff, int.Parse(roundOff));
                    }
                    else
                    {
                        // Dependent constraint: Strip enclosing braces and store the raw expressions
                        string strippedMinExpr = StripBraces(minExpr);
                        string strippedMaxExpr = StripBraces(maxExpr);

                        dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                            DataType: dataType, oneoff, int.Parse(roundOff));
                    }

                    dataTypes.Add(dataType);
                }
            }

            return (independentRanges, dependentConstraints, dataTypes);
        }


        /// <summary>
        /// Adjusts objects and attributes dynamically based on global attributes.
        /// </summary>
        /// <param name="environment">The environment to adjust.</param>
        private static void AdjustObjectsGlobally(Environment environment, bool isInitialTimeZero = false)
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


        /// <summary>
        /// Resolves constraints for attributes marked as mutable.
        /// </summary>
        private static (Dictionary<string, (double Min, double Max, string DataType, int RoundOff)> independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType, int RoundOff)> dependentConstraints,
            List<string> dataTypes)
            ResolveMutableConstraints(Environment baseEnv)
        {
            var independentRanges = new Dictionary<string, (double Min, double Max, string DataType, int RoundOff)>();
            var dependentConstraints =
                new Dictionary<string, (string MinExpr, string MaxExpr, string DataType, int RoundOff)>();
            var dataTypes = new List<string>();

            // Process global attributes
            foreach (var attr in baseEnv.Attributes.Where(attr => attr.Mutable.Value))
            {
                string attrName = attr.Name.Value;
                if (attrName != "Timestep_Count")
                {
                    continue;
                }

                string minExpr = attr.Constraint.Min ?? "0";
                string maxExpr = attr.Constraint.Max ?? "0";
                string dataType = attr.DataType.Value;
                string roundOff = string.IsNullOrEmpty(attr.Constraint.Choice) ? "0" : attr.Constraint.Choice;

                if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                {
                    independentRanges[attrName] = (double.Parse(minExpr), double.Parse(maxExpr), dataType,
                        int.Parse(roundOff));
                }
                else
                {
                    string strippedMinExpr = StripBraces(minExpr);
                    string strippedMaxExpr = StripBraces(maxExpr);

                    dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                        DataType: dataType, RoundOff: int.Parse(roundOff));
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
                    string roundOff = string.IsNullOrEmpty(attr.Constraint.Choice) ? "0" : attr.Constraint.Choice;

                    if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                    {
                        independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType,
                            int.Parse(roundOff));
                    }
                    else
                    {
                        string strippedMinExpr = StripBraces(minExpr);
                        string strippedMaxExpr = StripBraces(maxExpr);

                        dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                            DataType: dataType, RoundOff: int.Parse(roundOff));
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
        private static void ApplySamplesToEnvironment(Environment env, Dictionary<string, object> sample,
            List<string> dataTypes, bool isTimeStepTrue)
        {
            int dataTypeIndex = 0;

            foreach (var attr in env.Attributes.Where(attr => attr.Mutable.Value))
            {
                if (isTimeStepTrue && attr.Name.Value == "Timestep_Count")
                {
                    attr.Value.Content = Convert.ToString(0);
                }

                if (sample.ContainsKey(attr.Name.Value))
                {
                    attr.Value.Content = Convert.ToString(sample[attr.Name.Value]); // Convert object to string
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
                        attr.Value.Content = Convert.ToString(sample[sampleKey]); // Convert object to string
                        attr.DataType.Value = dataTypes.ElementAtOrDefault(dataTypeIndex++) ?? attr.DataType.Value;
                    }
                }
            }
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
    }
}