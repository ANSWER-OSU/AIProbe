using System;
using System.IO;

namespace AIprobe.Logging
{
    
    public static class Logger
    {
        private static string _logFilePath;

        // Initialize the logger with a file path
        public static void Initialize(string logFilePath)
        {
            _logFilePath = logFilePath;

            // Create or overwrite the log file at the start
            using (StreamWriter writer = new StreamWriter(_logFilePath, false))
            {
                writer.WriteLine($"Log initialized on {DateTime.Now}");
            }
        }

        // Log information messages
        public static void LogInfo(string message)
        {
            WriteLog("INFO", message);
        }

        // Log warning messages
        public static void LogWarning(string message)
        {
            WriteLog("WARNING", message);
        }

        // Log error messages
        public static void LogError(string message)
        {
            WriteLog("ERROR", message);
        }

        // Private method to write to the log file
        private static void WriteLog(string logLevel, string message)
        {
            using (StreamWriter writer = new StreamWriter(_logFilePath, true))
            {
                writer.WriteLine($"[{DateTime.Now}] {logLevel}: {message}");
            }
        }
    }
}