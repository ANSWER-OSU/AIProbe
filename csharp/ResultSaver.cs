using AIprobe.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;

namespace AIprobe
{
    public class ResultSaver
    {
        /// <summary>
        /// A class to represent the task result with instructions and the result ("yes" or "no")
        /// </summary>
        private class TaskResult
        {
            public List<string> Instructions { get; set; }
            public string Result { get; set; }
        }

        /// <summary>
        /// Save the result of the task in an env 
        /// </summary>
        /// <param name="taskResults"></param>
        /// <param name="filePath"></param>
        public static void SaveTaskResults(List<object[]> taskResults, string filePath)
        {
            // Dictionary to hold results to be saved in JSON format
            Dictionary<int, TaskResult> taskResultDict = new Dictionary<int, TaskResult>();
            int id = 1;

            // Process each result in taskResults
            foreach (var result in taskResults)
            {
                if (result.Length != 2)
                {
                    continue; // Ensure each result contains exactly 2 elements: instructions and result string
                }

                // Handle the first element (instructions)
                List<string> instructionSet;
                if (result[0] is string instruction) // If it's a single string
                {
                    instructionSet = new List<string> { instruction };
                }
                else if (result[0] is string[] instructionsArray) // If it's an array of strings
                {
                    instructionSet = new List<string>(instructionsArray);
                }
                else
                {
                    continue; // Skip if the format is unexpected
                }

                // Handle the second element (result status)
                string resultStatus = result[1] as string;

                if (resultStatus == null)
                {
                    continue; // Skip if result status is null or not a string
                }

                // Create a TaskResult object and store it
                TaskResult taskResult = new TaskResult
                {
                    Instructions = instructionSet,
                    Result = resultStatus
                };

                // Add the task result to the dictionary with the current taskId
                taskResultDict.Add(id, taskResult);

                // Increment the taskId
                id++;
            }

            // Save the task results to the JSON file
            ResultSaver resultSaver = new ResultSaver();
            resultSaver.SaveResultsToJson(filePath, taskResultDict);
        }

        /// <summary>
        /// Save the result to json format
        /// id:
        ///     "instructions": []
        ///     "result": "yes"
        /// </summary>
        /// <param name="filePath"></param>
        /// <param name="results"></param>
        private void SaveResultsToJson(string filePath, Dictionary<int, TaskResult> results)
        {
            try
            {
                // Serialize the dictionary to JSON format
                string json = JsonConvert.SerializeObject(results, Formatting.Indented);

                // Save JSON to a file
                File.WriteAllText(filePath, json);
                Logger.LogInfo($"Results successfully saved to {filePath}");
            }
            catch (Exception ex)
            {
                Logger.LogError($"Failed to save results to JSON: {ex.Message}");
            }
        }
    }
}
