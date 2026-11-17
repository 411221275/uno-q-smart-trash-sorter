#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;

void setup() {
  matrix.begin();
  matrix.clear();
  Bridge.begin();
}

void loop() {
  String text;
  bool ok = Bridge.call("get_trash_text").result(text);
  if (!ok) {
    text = "READY";
  }
  matrix.beginDraw();
  matrix.stroke(0xFFFFFFFF);
  matrix.textScrollSpeed(75);
  matrix.textFont(Font_5x7);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println("   " + text + "   ");
  matrix.endText(SCROLL_LEFT);
  matrix.endDraw();
}
