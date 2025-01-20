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
using AIprobe.TaskGenerator;

namespace AIprobe.EnvironmentGenerator
{
    using Attribute = AIprobe.Models.Attribute;
    using Environment = AIprobe.Models.Environment;
    using Object = AIprobe.Models.Object;

    public class EnvConfigGenerator
    {
        public static ConcurrentQueue<Environment> GenerateEnvConfigsQueue(Environment baseEnv, int? seed = null )
        {
            // Step 1: Resolve constraints into independent ranges and dependencies
            var (independentRanges, dependentConstraints, dataTypes) = ResolveConstraints(baseEnv);

            int nSamples = (independentRanges.Count + dependentConstraints.Count) * 10;
            //int nSamples = (independentRanges.Count) * 10;

            // Step 2: Perform LHS sampling with dependencies
            var sampledValues =
                LhsSampler.PerformLhsWithDependencies(independentRanges, dependentConstraints, nSamples, seed);

            // Step 3: Save sampled values to CSV
            SaveToCsv(sampledValues,
              $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/_values.csv");

            
            var randomsample = LhsSampler.PerformRandomSamplingWithDependencies(independentRanges, dependentConstraints, nSamples, seed);
            
            SaveToCsv(randomsample,
                $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/random_values.csv");
            
            
          
            var improvedLHS = LhsSampler.PerformLhsWithDependenciesImproved(independentRanges, dependentConstraints, nSamples, seed);
            
            SaveToCsv(improvedLHS,
                $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/improvedLHS_values.csv");
            
            // Use a queue instead of a list to store sampled environments
            ConcurrentQueue<Environment> sampledEnvironments = new ConcurrentQueue<Environment>();
            Aiprobe.LogAndDisplay($"Total no of environment generated: {sampledValues.Count}");
            int sampleCount = 0;
            EnvTaskGenerator gen = new EnvTaskGenerator();
            
            foreach (var sample in sampledValues)
            {
                
                var newEnv = CloneEnvironment(baseEnv); // Clone the base environment
                ApplySamplesToEnvironment(newEnv, sample, dataTypes);

                // Step 5: Adjust objects based on global attributes
                AdjustObjectsGlobally(newEnv);
                
                Environment modifiedEnv =  gen.MutateObjectProperties(newEnv);

                Aiprobe.LogAndDisplay($"Saved the generated sample env no: {sampledEnvironments.Count() + 1} in memory");
                
                // Enqueue the environment
                sampledEnvironments.Enqueue(modifiedEnv);
            }
            
            Aiprobe.LogAndDisplay($"Total no of environment generated and saved: {sampledEnvironments.Count}");
            return sampledEnvironments;

            // try
            // {
            //     Stopwatch totalStopwatch = new Stopwatch();
            //     totalStopwatch.Start();
            //
            //     ConcurrentQueue<Environment> newSampleEnvironments = new ConcurrentQueue<Environment>();
            //     int environmentCount = 1;
            //
            //     while (sampledEnvironments.Count > 0)
            //     {
            //         // Dequeue an environment for processing
            //         var env = sampledEnvironments.Dequeue();
            //
            //         Console.WriteLine($"Processing Environment no: {environmentCount}");
            //
            //         Stopwatch stopwatch = Stopwatch.StartNew();
            //
            //         var (independentRange, dependentConstraint) = ResolveAgentAndObjectConstraints(env);
            //         int nSample = (independentRange.Count + dependentConstraint.Count);
            //
            //         var sampledValue =
            //             LhsSampler.PerformLhsWithDependencies(independentRange, dependentConstraint, nSample, seed);
            //
            //         Parallel.ForEach(sampledValue, variable =>
            //         {
            //             var newEnv = CloneEnvironment(env); // Clone the base environment
            //             ApplySamplesToEnvironment(newEnv, variable, dataTypes);
            //
            //             // Enqueue the new environment
            //             lock (newSampleEnvironments)
            //             {
            //                 newSampleEnvironments.Enqueue(newEnv);
            //             }
            //         });
            //
            //         stopwatch.Stop();
            //         TimeSpan elapsed = stopwatch.Elapsed;
            //         Console.WriteLine($"Environment no: {environmentCount} took: {elapsed}");
            //         environmentCount++;
            //     }
            //
            //     totalStopwatch.Stop();
            //     Console.WriteLine($"Total time for processing all environments: {totalStopwatch.Elapsed}");
            //
            //     return newSampleEnvironments; // Return the queue
            // }
            // catch (COMException ex)
            // {
            //     Console.WriteLine($"Error HRESULT: {ex.ErrorCode}");
            //     Console.WriteLine($"Message: {ex.Message}");
            //     Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            //     throw;
            // }
        }


        public static List<Environment> GenerateEnvConfigs(Environment baseEnv, int? seed = null)
        {
            // Step 1: Resolve constraints into independent ranges and dependencies
            var (independentRanges, dependentConstraints, dataTypes) = ResolveConstraints(baseEnv);

            int nSamples = (independentRanges.Count + dependentConstraints.Count) * 10;

            // Step 2: Perform LHS sampling with dependencies
            var sampledValues =
                LhsSampler.PerformLhsWithDependencies(independentRanges, dependentConstraints, nSamples,
                    seed);

            // Step 3: Save sampled values to CSV
            SaveToCsv(sampledValues,
                $"/Users/rahil/Documents/GitHub/AIProbe/csharp/Result/re/{seed}/sampled_values.csv");

            var sampledEnvironments = new List<Environment>();
            foreach (var sample in sampledValues)
            {
                var newEnv = CloneEnvironment(baseEnv); // Clone the base environment
                ApplySamplesToEnvironment(newEnv, sample, dataTypes);


                // Step 5: Adjust objects based on global attributes
                AdjustObjectsGlobally(newEnv);


                sampledEnvironments.Add(newEnv);
            }

            var newSampleEnvironments = new List<Environment>();
            int Environmentcount = 1;
            try
            {
                Stopwatch totalStopwatch = new Stopwatch();
                totalStopwatch.Start();

                Parallel.ForEach(sampledEnvironments, env =>
                {
                    int envNumber;
                    lock (sampledEnvironments)
                    {
                        envNumber = Environmentcount++;

                        Console.WriteLine($"Processing Environment no: {envNumber}");
                    }

                    Stopwatch stopwatch = new Stopwatch();
                    stopwatch.Start();

                    var (independentRange, dependentConstraint) = ResolveAgentAndObjectConstraints(env);
                    int nSample = (independentRange.Count + dependentConstraint.Count);

                    var sampledValue =
                        LhsSampler.PerformLhsWithDependencies(independentRange, dependentConstraint, nSample,
                            seed);

                    Parallel.ForEach(sampledValue, VARIABLE =>
                    {
                        var newEnv = CloneEnvironment(env); // Clone the base environment
                        ApplySamplesToEnvironment(newEnv, VARIABLE, dataTypes);

                        // Thread-safe addition to collection
                        lock (newSampleEnvironments)
                        {
                            newSampleEnvironments.Add(newEnv);
                        }
                    });

                    stopwatch.Stop();
                    TimeSpan elapsed = stopwatch.Elapsed;

                    Console.WriteLine($"Environment no: {envNumber} took: {elapsed}");
                });

                totalStopwatch.Stop();
                Console.WriteLine($"Total time for processing all environments: {totalStopwatch.Elapsed}");
            }
            catch (COMException ex)
            {
                Console.WriteLine($"Error HRESULT: {ex.ErrorCode}");
                Console.WriteLine($"Message: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }


            // foreach (var env in sampledEnvironments)
            // {
            //     Console.WriteLine($"Enviroemnt no : {Environmentcount}");
            //     Stopwatch stopwatch = new Stopwatch();
            //     stopwatch.Start();
            //     var (independentRange, dependentConstraint) = ResolveAgentAndObjectConstraints(env);
            //
            //     int nSample = (independentRange.Count + dependentConstraint.Count) * 10;
            //
            //     var sampledValue =
            //         LhsSampler.PerformLhsWithDependencies(independentRange, dependentConstraint, nSample,
            //             seed);
            //
            //
            //     Parallel.ForEach(sampledValue, VARIABLE =>
            //     {
            //         var newEnv = CloneEnvironment(env); // Clone the base environment
            //         ApplySamplesToEnvironment(newEnv, VARIABLE, dataTypes);
            //
            //         // Use thread-safe collection or lock for shared resources
            //         lock (newSampleEnvironments)
            //         {
            //             newSampleEnvironments.Add(newEnv);
            //         }
            //     });
            //
            //     stopwatch.Stop();
            //
            //     // Get elapsed time
            //     TimeSpan elapsed = stopwatch.Elapsed;
            //
            //     Environmentcount += 1;
            //     Console.WriteLine($"took : {elapsed}");
            // }


            //     //     Console.WriteLine($"Environment Name: {env.Name}");
            //     //
            //     //     // Iterate through agents and print their attributes along with constraints
            //     //     Console.WriteLine("Agents:");
            //     //     foreach (var agent in env.Agents.AgentList)
            //     //     {
            //     //         Console.WriteLine($"\tAgent ID: {agent.Id}");
            //     //         foreach (var attr in agent.Attributes)
            //     //         {
            //     //             Console.WriteLine($"\t\tAttribute Name: {attr.Name.Value}, Value: {attr.Value.Content}, DataType: {attr.DataType.Value}");
            //     //             Console.WriteLine($"\t\t\tConstraints - Min: {attr.Constraint.Min}, Max: {attr.Constraint.Max}, OneOf: {attr.Constraint.OneOf}, RoundOff: {attr.Constraint.RoundOff}");
            //     //         }
            //     //     }
            //     //
            //     //     // Iterate through objects and print their attributes along with constraints
            //     //     Console.WriteLine("Objects:");
            //     //     foreach (var obj in env.Objects.ObjectList)
            //     //     {
            //     //         Console.WriteLine($"\tObject ID: {obj.Id}, Type: {obj.Type}");
            //     //         foreach (var attr in obj.Attributes)
            //     //         {
            //     //             Console.WriteLine($"\t\tAttribute Name: {attr.Name.Value}, Value: {attr.Value.Content}, DataType: {attr.DataType.Value}");
            //     //             Console.WriteLine($"\t\t\tConstraints - Min: {attr.Constraint.Min}, Max: {attr.Constraint.Max}, OneOf: {attr.Constraint.OneOf}, RoundOff: {attr.Constraint.RoundOff}");
            //     //         }
            //     //     }
            //     //
            //     //     // Print global attributes along with constraints
            //     //     Console.WriteLine("Global Attributes:");
            //     //     foreach (var attr in env.Attributes)
            //     //     {
            //     //         Console.WriteLine($"\tAttribute Name: {attr.Name.Value}, Value: {attr.Value.Content}, DataType: {attr.DataType.Value}");
            //     //         Console.WriteLine($"\t\tConstraints - Min: {attr.Constraint.Min}, Max: {attr.Constraint.Max}, OneOf: {attr.Constraint.OneOf}, RoundOff: {attr.Constraint.RoundOff}");
            //     //     }
            //     // }
            //     
            //     
            //     
            //     
            //     
            //     
            //     
            // }


            return newSampleEnvironments;
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


        private static (Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints)
            ClassifyConstraints(List<Attribute> attributes)
        {
            var independentRanges = new Dictionary<string, (double Min, double Max, string DataType)>();
            var dependentConstraints = new Dictionary<string, (string MinExpr, string MaxExpr, string DataType)>();

            foreach (var attr in attributes)
            {
                string attrName = attr.Name.Value;
                string minExpr = attr.Constraint.Min ?? "0";
                string maxExpr = attr.Constraint.Max ?? "0";
                string dataType = attr.DataType.Value;

                if (!ContainsGlobalAttribute(minExpr, "{") && !ContainsGlobalAttribute(maxExpr, "{"))
                {
                    // Independent constraint
                    independentRanges[attrName] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
                }
                else
                {
                    // Dependent constraint
                    dependentConstraints[attrName] = (MinExpr: minExpr, MaxExpr: maxExpr, DataType: dataType);
                }
            }

            return (independentRanges, dependentConstraints);
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


        public static (Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints,
            List<string> dataTypes)
            ResolveConstraints(Environment baseEnv)
        {
            var independentRanges = new Dictionary<string, (double Min, double Max, string DataType)>();
            var dependentConstraints = new Dictionary<string, (string MinExpr, string MaxExpr, string DataType)>();
            var dataTypes = new List<string>();

            foreach (var attr in baseEnv.Attributes)
            {
                string attrName = attr.Name.Value;
                string minExpr = attr.Constraint.Min ?? "0";
                string maxExpr = attr.Constraint.Max ?? "0";
                string dataType = attr.DataType.Value;

                if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                {
                    // Independent constraint
                    independentRanges[attrName] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
                }
                else
                {
                    // Dependent constraint: Strip enclosing braces and store the raw expressions
                    string strippedMinExpr = StripBraces(minExpr);
                    string strippedMaxExpr = StripBraces(maxExpr);

                    dependentConstraints[attrName] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                        DataType: dataType);
                }

                dataTypes.Add(dataType);
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


        public static (Dictionary<string, (double Min, double Max, string DataType)> independentRanges,
            Dictionary<string, (string MinExpr, string MaxExpr, string DataType)> dependentConstraints)
            ResolveAgentAndObjectConstraints(Environment baseEnv)
        {
            var independentRanges = new Dictionary<string, (double Min, double Max, string DataType)>();
            var dependentConstraints = new Dictionary<string, (string MinExpr, string MaxExpr, string DataType)>();

            // Process attributes of agents
            foreach (var agent in baseEnv.Agents.AgentList)
            {
                foreach (var attr in agent.Attributes)
                {
                    string key = $"Agent_{agent.Id}_{attr.Name.Value}";
                    string minExpr = attr.Constraint.Min ?? "0";
                    string maxExpr = attr.Constraint.Max ?? "0";
                    string dataType = attr.DataType.Value;

                    if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                    {
                        // Independent constraint
                        independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
                    }
                    else
                    {
                        // Dependent constraint: Strip enclosing braces and store the raw expressions
                        string strippedMinExpr = StripBraces(minExpr);
                        string strippedMaxExpr = StripBraces(maxExpr);

                        dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                            DataType: dataType);
                    }
                }
            }

            // Process attributes of objects
            foreach (var obj in baseEnv.Objects.ObjectList)
            {
                foreach (var attr in obj.Attributes)
                {
                    string key = $"Object_{obj.Id}_{attr.Name.Value}";
                    string minExpr = attr.Constraint.Min ?? "0";
                    string maxExpr = attr.Constraint.Max ?? "0";
                    string dataType = attr.DataType.Value;

                    if (!minExpr.Contains("{") && !maxExpr.Contains("{"))
                    {
                        // Independent constraint
                        independentRanges[key] = (double.Parse(minExpr), double.Parse(maxExpr), dataType);
                    }
                    else
                    {
                        // Dependent constraint: Strip enclosing braces and store the raw expressions
                        string strippedMinExpr = StripBraces(minExpr);
                        string strippedMaxExpr = StripBraces(maxExpr);

                        dependentConstraints[key] = (MinExpr: strippedMinExpr, MaxExpr: strippedMaxExpr,
                            DataType: dataType);
                    }
                }
            }

            return (independentRanges, dependentConstraints);
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


        public static List<Dictionary<string, double>> PerformLhsWithDependencies(
            Dictionary<string, (double Min, double Max)> independentRanges,
            Dictionary<string, Func<Dictionary<string, double>, (double Min, double Max)>> dependencies,
            int nSamples,
            int? seed = null)
        {
            var random = seed.HasValue ? new Random(seed.Value) : new Random();

            // Step 1: Initialize stratified intervals for independent parameters
            var stratifiedIntervals = new Dictionary<string, List<double>>();
            foreach (var (key, (minValue, maxValue)) in independentRanges)
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
                foreach (var key in independentRanges.Keys)
                {
                    double intervalStart = stratifiedIntervals[key][i];
                    double intervalWidth = (independentRanges[key].Max - independentRanges[key].Min) / nSamples;
                    sample[key] = intervalStart + random.NextDouble() * intervalWidth;
                }

                lhsSamples.Add(sample);
            }

            // Step 3: Resolve dependent parameters dynamically
            foreach (var (key, dependencyFunction) in dependencies)
            {
                for (int i = 0; i < nSamples; i++)
                {
                    // Resolve range dynamically based on already sampled independent values
                    var (min, max) = dependencyFunction(lhsSamples[i]);
                    double intervalWidth = (max - min) / nSamples;

                    // Stratify and sample the dependent parameter
                    double intervalStart = min + i * intervalWidth;
                    lhsSamples[i][key] = intervalStart + random.NextDouble() * intervalWidth;
                }
            }

            return lhsSamples;
        }

        // private static void ApplySamplesToEnvironment(Environment env, Dictionary<string, double> sample,
        //     List<string> dataTypes)
        // {
        //     int index = 0;
        //     foreach (var attr in env.Attributes)
        //     {
        //         attr.Value.Content = Convert.ToString(sample[attr.Name.Value]);
        //         attr.DataType.Value = dataTypes[index++];
        //     }
        //     
        // }


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
                    string sampleKey = $"Object_{obj.Id}_{attr.Name.Value}";
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