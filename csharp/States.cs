using AIprobe.Models;
using System;
using System.Collections.Generic;
using Environment = AIprobe.Models.Environment;
using Attribute = AIprobe.Models.Attribute;

namespace AIprobe
{
    public class States
    {
        public List<object[]> CreateInitialState(Environment environment)
        {
            List<object[]> initialState = new List<object[]>();

            // Parse Agents
            if (environment.Agents != null && environment.Agents.AgentList != null)
            {
                foreach (var agent in environment.Agents.AgentList)
                {
                    object x = 0, y = 0, z = 0;

                    foreach (var attribute in agent.Position.Attributes)
                    {
                        if (attribute.Name.Value == "X")
                        {
                            x = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                        else if (attribute.Name.Value == "Y")
                        {
                            y = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                        else if (attribute.Name.Value == "Z")
                        {
                            z = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                    }

                    object[] position = new object[] { x, y, z };
                    string direction = agent.Direction.Attribute.Value.ToString();

                    // Add the agent state
                    initialState.Add(new object[] { "Agent", agent.Id, position, direction });
                }
            }

            // Parse Objects
            if (environment.Objects != null && environment.Objects.ObjectList != null)
            {
                foreach (var obj in environment.Objects.ObjectList)
                {
                    object x = 0, y = 0, z = 0;

                    foreach (var attribute in obj.Position.Attributes)
                    {
                        if (attribute.Name.Value == "X")
                        {
                            x = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                        else if (attribute.Name.Value == "Y")
                        {
                            y = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                        else if (attribute.Name.Value == "Z")
                        {
                            z = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                    }

                    object[] position = new object[] { x, y, z };

                    // Add the object state
                    initialState.Add(new object[] { "Object", obj.Id, position });
                }
            }

            // Parse Environment Properties
            if (environment.EnvironmentalProperties != null && environment.EnvironmentalProperties.Properties != null)
            {
                foreach (var property in environment.EnvironmentalProperties.Properties)
                {
                    object width = 0, height = 0, depth = 0;

                    foreach (var attribute in property.Attributes)
                    {
                        if (attribute.Name.Value == "Width")
                        {
                            width = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                        else if (attribute.Name.Value == "Height")
                        {
                            height = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                        else if (attribute.Name.Value == "Depth")
                        {
                            depth = ParseValueByDataType(attribute); // Parse based on DataType
                        }
                    }

                    // Add environment property
                    initialState.Add(new object[] { "Property", property.Name.ToString(), new object[] { width, height, depth } });
                }
            }

            return initialState;
        }

        // Helper method to parse the value based on its DataType
        private object ParseValueByDataType(Attribute attribute)
        {
            string dataType = attribute.DataType.Value;

            switch (dataType)
            {
                case "integer":
                    return Convert.ToInt32(attribute.Value.ValueData);
                case "float":
                    return Convert.ToSingle(attribute.Value.ValueData);
                case "string":
                    return attribute.Value.ValueData.ToString();
                case "boolean":
                    return Convert.ToBoolean(attribute.Value.ValueData);
                default:
                    return attribute.Value.ValueData; // Return as is for unsupported types
            }
        }
    }
}
