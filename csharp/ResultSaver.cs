using AIprobe.Logging;
using Newtonsoft.Json;

namespace AIprobe;

/// <summary>
/// 
/// </summary>
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
            string[] instructionSet = (string[])result[0];
            string resultStatus = (string)result[1];

            // Create a TaskResult object and store it
            TaskResult taskResult = new TaskResult
            {
                Instructions = new List<string>(instructionSet),
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
    ///      "result": "yes"
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