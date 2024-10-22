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

            try
            {
                // Check if the directory exists
                string logDirectory = Path.GetDirectoryName(logFilePath);
                if (!Directory.Exists(logDirectory))
                {
                    Console.WriteLine($"Directory does not exist. Creating: {logDirectory}");
                    Directory.CreateDirectory(logDirectory);
                }

                // Create or overwrite the log file at the start
                using (StreamWriter writer = new StreamWriter(_logFilePath, false))
                {
                    writer.WriteLine($"Log initialized on {DateTime.Now}");
                }

                Console.WriteLine($"Log file successfully initialized at: {_logFilePath}");
            }
            catch (UnauthorizedAccessException ex)
            {
                Console.WriteLine("Error: Access to the path is denied. Please check permissions.");
                Console.WriteLine(ex.Message);
            }
            catch (DirectoryNotFoundException ex)
            {
                Console.WriteLine("Error: The directory could not be found. Please check the log path.");
                Console.WriteLine(ex.Message);
            }
            catch (IOException ex)
            {
                Console.WriteLine("I/O Error: Could not create or write to the log file.");
                Console.WriteLine(ex.Message);
            }
            catch (Exception ex)
            {
                Console.WriteLine("An unexpected error occurred while initializing the log file.");
                Console.WriteLine(ex.Message);
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