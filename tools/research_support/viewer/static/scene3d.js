/* Minimal 3-D projector for the inspection view.
 *
 * This is deliberately a projector, not a rendering engine: a rotation, a perspective
 * divide, a depth sort and the same 2-D drawing primitives the default view uses. It reads
 * the same frame data as the 2-D scene and never asks for another environment step or
 * radio solve.
 *
 * Axes are labelled and the vertical exaggeration factor is shown; the default is true
 * scale. Missing elevation geometry stays a flat-ground model -- no terrain is invented.
 */
(function (global) {
  "use strict";

  function Camera(bounds) {
    this.bounds = bounds;                 // [minX, minY, maxX, maxY] in metres
    this.azimuth = -0.62;                 // radians, around the vertical axis
    this.elevation = 0.52;                // radians above the ground plane
    this.distanceScale = 2.3;             // multiples of the scene half-extent
    this.zExaggeration = 1.0;
    this.panX = 0;
    this.panY = 0;
  }

  Camera.prototype.reset = function () {
    this.azimuth = -0.62;
    this.elevation = 0.52;
    this.distanceScale = 2.3;
    this.panX = 0;
    this.panY = 0;
  };

  Camera.prototype.topDown = function () {
    this.azimuth = 0;
    this.elevation = Math.PI / 2 - 0.001;
    this.panX = 0;
    this.panY = 0;
  };

  Camera.prototype.orbit = function (dAz, dEl) {
    this.azimuth += dAz;
    var limit = Math.PI / 2 - 0.02;
    this.elevation = Math.max(0.04, Math.min(limit, this.elevation + dEl));
  };

  Camera.prototype.zoom = function (factor) {
    this.distanceScale = Math.max(0.6, Math.min(12, this.distanceScale * factor));
  };

  /* Centre of the scene in world metres; z centre is kept at ground level so altitude
   * reads upward from the plane the UEs sit on. */
  Camera.prototype.centre = function () {
    var b = this.bounds;
    return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, 0];
  };

  Camera.prototype.halfExtent = function () {
    var b = this.bounds;
    return Math.max(1, Math.max(b[2] - b[0], b[3] - b[1]) / 2);
  };

  /* Project one world point to canvas pixels.
   * Returns {x, y, depth, visible}. depth is distance from the eye, for sorting. */
  Camera.prototype.project = function (p, width, height) {
    var c = this.centre();
    var half = this.halfExtent();
    var ex = (p[0] - c[0]) / half;
    var ey = (p[1] - c[1]) / half;
    var ez = ((p[2] || 0) * this.zExaggeration) / half;

    var ca = Math.cos(this.azimuth), sa = Math.sin(this.azimuth);
    var rx = ex * ca - ey * sa;
    var ry = ex * sa + ey * ca;

    var ce = Math.cos(this.elevation), se = Math.sin(this.elevation);
    // Camera looks down the +depth axis; screen-up combines world z and the tilted y.
    var depthAxis = ry * ce + ez * se;
    var upAxis = -ry * se + ez * ce;

    var eye = this.distanceScale;
    var d = eye - depthAxis;
    if (d < 0.05) { return { x: 0, y: 0, depth: d, visible: false }; }

    var focal = 1.15;
    var scale = (Math.min(width, height) * 0.42) * focal / d;
    return {
      x: width / 2 + rx * scale + this.panX,
      y: height / 2 - upAxis * scale + this.panY,
      depth: d,
      visible: true,
      scale: scale / (Math.min(width, height) * 0.42)
    };
  };

  /* Draw the ground plane box, axis ticks and a metre scale. */
  Camera.prototype.drawGround = function (ctx, width, height, tokens) {
    var b = this.bounds;
    var corners = [
      [b[0], b[1], 0], [b[2], b[1], 0], [b[2], b[3], 0], [b[0], b[3], 0]
    ].map(function (p) { return this.project(p, width, height); }, this);
    if (corners.some(function (c) { return !c.visible; })) { return; }

    ctx.save();
    ctx.strokeStyle = tokens.line;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    for (var i = 1; i < corners.length; i += 1) { ctx.lineTo(corners[i].x, corners[i].y); }
    ctx.closePath();
    ctx.stroke();

    // Grid lines every 1/4 of the extent, so distance is readable.
    ctx.strokeStyle = tokens.line2;
    ctx.setLineDash([2, 4]);
    for (var k = 1; k < 4; k += 1) {
      var fx = b[0] + (b[2] - b[0]) * k / 4;
      var fy = b[1] + (b[3] - b[1]) * k / 4;
      var a = this.project([fx, b[1], 0], width, height);
      var c = this.project([fx, b[3], 0], width, height);
      var e = this.project([b[0], fy, 0], width, height);
      var f = this.project([b[2], fy, 0], width, height);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(c.x, c.y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(e.x, e.y); ctx.lineTo(f.x, f.y); ctx.stroke();
    }
    ctx.setLineDash([]);

    // Axis labels in metres at two corners.
    ctx.fillStyle = tokens.ink3;
    ctx.font = "11px " + tokens.mono;
    ctx.fillText("x " + Math.round(b[0]) + "-" + Math.round(b[2]) + " m", corners[0].x + 4, corners[0].y + 12);
    ctx.fillText("y " + Math.round(b[1]) + "-" + Math.round(b[3]) + " m", corners[3].x + 4, corners[3].y - 4);
    ctx.restore();
  };

  /* Vertical stalk from the ground to an airborne entity, so altitude is legible. */
  Camera.prototype.drawStalk = function (ctx, p, width, height, tokens) {
    var top = this.project(p, width, height);
    var base = this.project([p[0], p[1], 0], width, height);
    if (!top.visible || !base.visible) { return null; }
    ctx.save();
    ctx.strokeStyle = tokens.line;
    ctx.setLineDash([1, 3]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(base.x, base.y);
    ctx.lineTo(top.x, top.y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
    return top;
  };

  global.RSScene3D = { Camera: Camera };
}(window));
